from __future__ import annotations

import hashlib
import logging
import threading
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, Optional

from django.conf import settings
from django.db import close_old_connections, transaction
from django.db.models import Q
from django.utils import timezone

from main.execution_engine import ContractInfo, ExecutionRequest, get_execution_engine
from main.broker_instrument_cache import load_upstox_instruments
from main.models import (
    ClientBrokerdetails,
    ClientTradeSetting,
    GroupService,
    ManualTradeBatch,
    ManualTradeResult,
    User,
)
from main.permissions import get_accessible_clients_queryset, is_admin_or_superadmin, is_subadmin_user
from main.services.live_price_cache import get_live_price
from main.services.trade_limit import successful_buy_count


ACTION_TO_ORDER = {
    ManualTradeBatch.ACTION_BUY_CE: ("BUY", "CE"),
    ManualTradeBatch.ACTION_BUY_PE: ("BUY", "PE"),
}

logger = logging.getLogger(__name__)
_dispatcher = None
_dispatcher_lock = threading.Lock()


def _get_manual_trade_dispatcher() -> ThreadPoolExecutor:
    """Return the process-local, bounded broker-call executor.

    The pool is created lazily so it is safe when gunicorn preloads the Django
    application before forking workers. A bounded worker count prevents a large
    batch from exhausting database connections or broker/node sockets.
    """
    global _dispatcher
    if _dispatcher is None:
        with _dispatcher_lock:
            if _dispatcher is None:
                worker_count = max(1, int(getattr(settings, "MANUAL_TRADE_DISPATCH_WORKERS", 32) or 32))
                _dispatcher = ThreadPoolExecutor(
                    max_workers=worker_count,
                    thread_name_prefix="manual-trade",
                )
    return _dispatcher


def _normalize_symbol(value: Any) -> str:
    return str(value or "").strip().upper()


def _decimal_strike(value: Any) -> Decimal:
    try:
        strike = Decimal(str(value).strip())
    except (InvalidOperation, AttributeError):
        raise ValueError("Strike price must be a valid number.")
    if strike <= 0:
        raise ValueError("Strike price must be greater than zero.")
    return strike.quantize(Decimal("0.01"))


def _date_parts(expiry_date):
    if not expiry_date:
        return "", "", "", ""
    if timezone.is_aware(expiry_date):
        expiry_date = timezone.localtime(expiry_date)
    return (
        f"{expiry_date.day:02d}",
        expiry_date.strftime("%b"),
        expiry_date.strftime("%y"),
        str(expiry_date.year),
    )


def _local_expiry(expiry_date):
    if not expiry_date:
        return None
    return timezone.localtime(expiry_date) if timezone.is_aware(expiry_date) else expiry_date


def _local_expiry_date(expiry_date):
    if not expiry_date:
        return None
    if timezone.is_naive(expiry_date):
        expiry_date = timezone.make_aware(expiry_date)
    return timezone.localtime(expiry_date).date()


def _manual_trade_live_price(batch: ManualTradeBatch, setting: ClientTradeSetting, option_type: str) -> tuple[Decimal, str]:
    """Use the shared WebSocket premium without adding a broker quote round trip."""
    payload = get_live_price(
        underlying=batch.symbol,
        expiry_date=_local_expiry_date(setting.expiry_date),
        strike=batch.strike_price,
        option_type=option_type,
        max_age_seconds=15,
    )
    if isinstance(payload, dict) and payload.get("is_fresh"):
        try:
            ltp = Decimal(str(payload.get("ltp")))
        except (InvalidOperation, TypeError):
            ltp = Decimal("0")
        if ltp > 0:
            return ltp.quantize(Decimal("0.01")), "central_live_price_cache"
    # Broker adapters still perform their own required validation. The strike is
    # only a reference here and is never treated as the final executed price.
    return Decimal(str(batch.strike_price)).quantize(Decimal("0.01")), "broker_adapter_live_price"


def _client_name(client) -> str:
    return (
        getattr(client, "fullName", None)
        or " ".join(part for part in [getattr(client, "firstName", None), getattr(client, "lastName", None)] if part)
        or getattr(client, "email", None)
        or f"Client #{getattr(client, 'id', '')}"
    )


def _broker_status(client, trade_setting, broker_details_list=None) -> Dict[str, Any]:
    broker_name = str(getattr(trade_setting, "broker", "") or "").strip()
    if not broker_name:
        return {"ready": False, "broker": "", "reason": "Broker is not selected in client saved script setting."}

    available_details = list(broker_details_list) if broker_details_list is not None else list(
        ClientBrokerdetails.objects.select_related("broker_name", "execution_node").filter(client=client)
    )
    broker_detail = next(
        (
            details for details in available_details
            if str(getattr(getattr(details, "broker_name", None), "broker_name", "") or "").strip().casefold()
            == broker_name.casefold()
        ),
        None,
    )
    if not broker_detail:
        broker_detail = available_details[0] if available_details else None
    if not broker_detail:
        return {"ready": False, "broker": broker_name, "reason": "Broker details are not configured for this client."}

    resolved_broker = getattr(getattr(broker_detail, "broker_name", None), "broker_name", None) or broker_name
    if not (broker_detail.get_access_token_secure() or broker_detail.access_token):
        return {"ready": False, "broker": resolved_broker, "reason": "Broker access token is missing. Client must login to broker again."}
    if getattr(broker_detail, "isTokenExpired", False):
        return {"ready": False, "broker": resolved_broker, "reason": "Broker token is marked expired. Client must login to broker again."}
    if broker_detail.access_token_expiry and broker_detail.access_token_expiry <= timezone.now():
        return {"ready": False, "broker": resolved_broker, "reason": "Broker access token has expired. Client must login to broker again."}
    if not broker_detail.execution_node_id:
        return {"ready": False, "broker": resolved_broker, "reason": "No verified execution IP/node is assigned for this broker."}
    return {"ready": True, "broker": resolved_broker, "reason": "Ready"}


def _matching_trade_settings(group_service: GroupService, symbol: str, actor) -> Iterable[ClientTradeSetting]:
    accessible_clients = get_accessible_clients_queryset(actor)
    return (
        ClientTradeSetting.objects.select_related("client", "segment", "sub_segment")
        .filter(client__in=accessible_clients)
        .filter(client__Group_service_id=group_service.id)
        .filter(Q(group_service__iexact=group_service.group_name) | Q(group_service__isnull=True) | Q(group_service=""))
        .filter(Q(symbol__iexact=symbol) | Q(sub_segment__name__iexact=symbol) | Q(sub_segment__short_name__iexact=symbol))
        .order_by("client_id", "-updated_at", "-id")
    )


def _select_one_setting_per_client(settings_queryset) -> list[ClientTradeSetting]:
    selected = []
    seen_clients = set()
    for setting in settings_queryset:
        if setting.client_id in seen_clients:
            continue
        seen_clients.add(setting.client_id)
        selected.append(setting)
    return selected


def _result_snapshot(setting: Optional[ClientTradeSetting], broker_info: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    client = setting.client if setting else None
    expiry = _local_expiry_date(getattr(setting, "expiry_date", None))
    return {
        "client_id": getattr(client, "id", None),
        "client_name": _client_name(client) if client else "",
        "email": getattr(client, "email", None),
        "broker": (broker_info or {}).get("broker") or getattr(setting, "broker", None),
        "broker_ready": (broker_info or {}).get("ready", False),
        "trade_setting_id": getattr(setting, "id", None),
        "saved_symbol": getattr(setting, "symbol", None),
        "expiry_date": expiry.isoformat() if expiry else None,
        "order_type": getattr(setting, "order_type", None),
        "product_type": getattr(setting, "product_type", None),
        "quantity": getattr(setting, "quantity", None),
        "trade_limit": getattr(setting, "trade_limit", None),
        "is_tread_status": getattr(setting, "is_tread_status", None),
    }


def _eligibility_reason(setting: ClientTradeSetting, broker_info: Dict[str, Any]) -> Optional[str]:
    client = setting.client
    if not getattr(client, "is_active", False):
        return "Client login is inactive."
    client_status = getattr(client, "client_status", None)
    if isinstance(client_status, str) and client_status.strip() and client_status.strip().lower() not in {"active", "enabled"}:
        return f"Client status is {client_status}."
    if isinstance(client_status, bool) and client_status is False:
        return "Client status is inactive."
    if not setting.is_tread_status:
        return "Client saved script trading status is disabled."
    if not setting.expiry_date:
        return "Expiry is not saved in client script setting."
    if not setting.quantity or int(setting.quantity or 0) <= 0:
        return "Quantity is not saved in client script setting."
    if not str(setting.order_type or "").strip():
        return "Order type is not saved in client script setting."
    if not str(setting.product_type or "").strip():
        return "Product type is not saved in client script setting."
    configured_limit = int(setting.trade_limit or 0)
    if configured_limit > 0:
        successful_count = successful_buy_count(client, setting.symbol)
        if successful_count >= configured_limit:
            return f"Daily successful BUY trade limit reached ({successful_count}/{configured_limit})."
    if not broker_info.get("ready"):
        return broker_info.get("reason") or "Broker is not ready."
    return None


def _upstox_contract_reason(setting: ClientTradeSetting, symbol: str, strike: Decimal, option_type: str) -> Optional[str]:
    if str(setting.broker or "").strip().lower() != "upstox" or not setting.expiry_date:
        return None
    try:
        expiry = timezone.localtime(setting.expiry_date).date()
        candidates = []
        for instrument in load_upstox_instruments("NSE"):
            if str(instrument.get("underlying_symbol") or "").strip().upper() != symbol:
                continue
            if str(instrument.get("instrument_type") or "").strip().upper() != option_type:
                continue
            instrument_expiry = datetime.fromtimestamp(
                float(instrument.get("expiry")) / 1000,
                tz=datetime_timezone.utc,
            ).date()
            if instrument_expiry == expiry:
                candidates.append(Decimal(str(instrument.get("strike_price"))))
        if not candidates or strike in candidates:
            return None
        nearest = sorted(set(candidates), key=lambda value: (abs(value - strike), value))[:2]
        nearest_text = " or ".join(f"{value:g}" for value in sorted(nearest))
        return (
            f"Strike {strike:g} is not available for {symbol} {option_type} expiring "
            f"{expiry:%d %b %Y}. Select {nearest_text}."
        )
    except Exception:
        # A stale/unavailable reference file must not prevent otherwise valid orders.
        return None


def build_manual_trade_idempotency_key(company_id, group_service_id, symbol, action, strike_price) -> str:
    payload = "|".join([
        str(company_id or "platform"),
        str(group_service_id),
        _normalize_symbol(symbol),
        str(action),
        str(strike_price),
        timezone.localtime().strftime("%Y%m%d%H%M"),
    ])
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:48]


def create_manual_trade_preview(*, actor, group_service_id, symbol, action, strike_price) -> ManualTradeBatch:
    symbol = _normalize_symbol(symbol)
    if not symbol:
        raise ValueError("Script is required.")
    if action not in ACTION_TO_ORDER:
        raise ValueError("Manual trade action must be BUY_CE or BUY_PE.")
    strike = _decimal_strike(strike_price)

    group_queryset = GroupService.objects.all()
    if is_subadmin_user(actor):
        group_queryset = group_queryset.filter(group_Service__in=get_accessible_clients_queryset(actor)).distinct()
    elif not is_admin_or_superadmin(actor):
        group_queryset = group_queryset.none()
    group_service = group_queryset.get(pk=group_service_id)

    settings = _select_one_setting_per_client(_matching_trade_settings(group_service, symbol, actor))
    broker_details_by_client = defaultdict(list)
    if settings:
        broker_details = ClientBrokerdetails.objects.select_related("broker_name", "execution_node").filter(
            client_id__in=[setting.client_id for setting in settings]
        )
        for broker_detail in broker_details:
            broker_details_by_client[broker_detail.client_id].append(broker_detail)
    idempotency_key = build_manual_trade_idempotency_key(
        None,
        group_service.id,
        symbol,
        action,
        strike,
    )

    with transaction.atomic():
        batch = ManualTradeBatch.objects.create(
            requested_by=actor,
            group_service=group_service,
            symbol=symbol,
            action=action,
            strike_price=strike,
            idempotency_key=idempotency_key,
            input_snapshot={
                "symbol": symbol,
                "action": action,
                "strike_price": str(strike),
                "group_service_id": group_service.id,
                "group_service": group_service.group_name,
                "source": "manual_trade",
            },
        )

        eligible_count = 0
        skipped_count = 0
        result_rows = []
        for setting in settings:
            broker_info = _broker_status(
                setting.client,
                setting,
                broker_details_list=broker_details_by_client.get(setting.client_id, []),
            )
            reason = _eligibility_reason(setting, broker_info)
            if not reason:
                reason = _upstox_contract_reason(setting, symbol, strike, ACTION_TO_ORDER[action][1])
            status = ManualTradeResult.STATUS_SKIPPED if reason else ManualTradeResult.STATUS_PENDING
            if reason:
                skipped_count += 1
            else:
                eligible_count += 1
            result_rows.append(ManualTradeResult(
                batch=batch,
                client=setting.client,
                trade_setting=setting,
                broker=broker_info.get("broker") or setting.broker,
                status=status,
                reason=reason,
                request_snapshot=_result_snapshot(setting, broker_info),
            ))

        ManualTradeResult.objects.bulk_create(result_rows, batch_size=500)

        batch.preview_count = len(settings)
        batch.eligible_count = eligible_count
        batch.skipped_count = skipped_count
        batch.summary = {
            "preview_count": len(settings),
            "eligible_count": eligible_count,
            "skipped_count": skipped_count,
        }
        batch.save(update_fields=["preview_count", "eligible_count", "skipped_count", "summary", "updated_at"])
    return batch


def _build_execution_request(result: ManualTradeResult) -> ExecutionRequest:
    batch = result.batch
    setting = result.trade_setting
    transaction_type, option_type = ACTION_TO_ORDER[batch.action]
    live_price, live_price_source = _manual_trade_live_price(batch, setting, option_type)
    expiry = _local_expiry(setting.expiry_date)
    expiry_date = _local_expiry_date(setting.expiry_date)
    day, month, year, fullyear = _date_parts(expiry)
    history_id = f"manual_{batch.id}_{result.client_id}_{timezone.now().strftime('%Y%m%d%H%M%S%f')}"
    order_params = {
        "source": "manual_trade",
        "manual_trade_batch_id": batch.id,
        "manual_trade_result_id": result.id,
        "trade_setting_id": setting.id,
        "symbol": batch.symbol,
        "underlying": batch.symbol,
        "strike": float(batch.strike_price),
        "strike_price": float(batch.strike_price),
        "default_price": float(batch.strike_price),
        "option_type": option_type,
        "Type": option_type,
        "quantity": setting.quantity,
        "expiry": expiry_date.isoformat() if expiry_date else None,
        "order_type": setting.order_type,
        "product_type": setting.product_type,
        "buffer_percentage": float(setting.buffer_percentage) if setting.buffer_percentage is not None else None,
        "ltp": float(live_price),
        "manual_trade_price_source": live_price_source,
        "idempotency_key": f"manual:{batch.id}:{result.client_id}",
    }
    return ExecutionRequest(
        LivePrice=live_price,
        group_service=batch.group_service.group_name,
        trade=setting,
        user=result.client,
        transaction_type=transaction_type,
        symbol=batch.symbol,
        quantity=int(setting.quantity or 0),
        strategy="Trade Execution",
        ordertype=setting.order_type or "LIMIT",
        product_type=setting.product_type or "INTRADAY",
        price=None,
        Lots=1,
        trade_order_status="OPEN",
        Entry_type=transaction_type,
        Exit_type=None,
        Entry_price=None,
        Exit_price=None,
        EntryQty=int(setting.quantity or 0),
        ExitQty=None,
        webhook_signal={
            "source": "manual_trade",
            "manual_trade_batch_id": batch.id,
            "manual_trade_result_id": result.id,
            "initiated_by": getattr(batch.requested_by, "id", None),
        },
        Exchange=getattr(getattr(setting, "sub_segment", None), "Exchange", None) or "NFO",
        Segment=getattr(getattr(setting, "segment", None), "name", None),
        Index_Symbol=batch.symbol,
        triggerPrice=0,
        day=day,
        month=month,
        year=year,
        fullyear=fullyear,
        strike=batch.strike_price,
        option_type=option_type,
        order_params=order_params,
        history_id=history_id,
        contract_info=ContractInfo(
            symbol=batch.symbol,
            strike=float(batch.strike_price),
            option_type=option_type,
            exchange=getattr(getattr(setting, "sub_segment", None), "Exchange", None) or "NFO",
            expiry=expiry,
        ),
    )


def _finalize_manual_trade_batch(batch_id: int) -> Dict[str, Any]:
    """Refresh aggregate state; row locking makes concurrent completions safe."""
    unfinished = ManualTradeResult.objects.filter(
        batch_id=batch_id,
        status__in=[ManualTradeResult.STATUS_PENDING, ManualTradeResult.STATUS_PROCESSING],
    ).exists()
    if unfinished:
        return {"status": ManualTradeBatch.STATUS_PROCESSING}

    with transaction.atomic():
        batch = ManualTradeBatch.objects.select_for_update().get(pk=batch_id)
        success_count = batch.results.filter(status=ManualTradeResult.STATUS_SUCCESS).count()
        failed_count = batch.results.filter(status=ManualTradeResult.STATUS_FAILED).count()
        skipped_count = batch.results.filter(status=ManualTradeResult.STATUS_SKIPPED).count()
        pending_count = batch.results.filter(
            status__in=[ManualTradeResult.STATUS_PENDING, ManualTradeResult.STATUS_PROCESSING]
        ).count()
        if pending_count:
            status_value = ManualTradeBatch.STATUS_PROCESSING
        elif failed_count and success_count:
            status_value = ManualTradeBatch.STATUS_PARTIAL
        elif failed_count and not success_count:
            status_value = ManualTradeBatch.STATUS_FAILED
        else:
            status_value = ManualTradeBatch.STATUS_COMPLETED
        batch.success_count = success_count
        batch.failed_count = failed_count
        batch.skipped_count = skipped_count
        batch.status = status_value
        batch.completed_at = timezone.now() if not pending_count else None
        batch.summary = {
            "success_count": success_count,
            "failed_count": failed_count,
            "skipped_count": skipped_count,
            "pending_count": pending_count,
        }
        batch.save(update_fields=["success_count", "failed_count", "skipped_count", "status", "completed_at", "summary", "updated_at"])
        return {"status": batch.status, "summary": batch.summary}


def _execute_manual_trade_result(result_id: int) -> None:
    """Atomically claim and execute one client order."""
    close_old_connections()
    try:
        claimed = ManualTradeResult.objects.filter(
            pk=result_id,
            status=ManualTradeResult.STATUS_PENDING,
        ).update(
            status=ManualTradeResult.STATUS_PROCESSING,
            reason="Order is being sent.",
            updated_at=timezone.now(),
        )
        if not claimed:
            return
        result = ManualTradeResult.objects.select_related(
            "batch", "batch__group_service", "batch__requested_by", "client",
            "trade_setting", "trade_setting__segment", "trade_setting__sub_segment",
        ).get(pk=result_id)
        execution_request = _build_execution_request(result)
        result.history_id = execution_request.history_id
        result.request_snapshot = {
            **(result.request_snapshot or {}),
            "history_id": execution_request.history_id,
            "order_params": execution_request.order_params,
        }
        result.save(update_fields=["history_id", "request_snapshot", "updated_at"])

        response = get_execution_engine().execute_order(execution_request)
        data = response.get("data", {}) if isinstance(response, dict) else {}
        broker_status = str(data.get("status") or response.get("status") or "").strip()
        normalized_broker_status = broker_status.lower()
        success = normalized_broker_status in {"success", "complete", "completed", "executed", "traded", "filled"}
        accepted = normalized_broker_status in {
            "open", "pending", "transit", "placed", "accepted_by_node", "sent_to_node",
        }
        if success:
            result.status = ManualTradeResult.STATUS_SUCCESS
        elif accepted:
            result.status = ManualTradeResult.STATUS_PROCESSING
        else:
            result.status = ManualTradeResult.STATUS_FAILED
        result.broker_status = broker_status
        result.order_id = data.get("order_id") or data.get("orderid") or data.get("job_id")
        result.reason = (
            data.get("message")
            or data.get("error")
            or ("Order sent." if success or accepted else "Broker rejected the order.")
        )
        result.response_snapshot = response if isinstance(response, dict) else {"response": str(response)}
        result.save(update_fields=["status", "broker_status", "order_id", "reason", "response_snapshot", "updated_at"])
    except Exception as exc:
        logger.exception("Immediate manual trade execution failed result_id=%s", result_id)
        ManualTradeResult.objects.filter(pk=result_id).update(
            status=ManualTradeResult.STATUS_FAILED,
            reason=str(exc),
            response_snapshot={"error": str(exc)},
            updated_at=timezone.now(),
        )
    finally:
        try:
            batch_id = ManualTradeResult.objects.values_list("batch_id", flat=True).get(pk=result_id)
            _finalize_manual_trade_batch(batch_id)
        except Exception:
            logger.exception("Could not finalize immediate manual trade result_id=%s", result_id)
        close_old_connections()


def dispatch_manual_trade_batch(batch_id: int) -> Dict[str, Any]:
    """Submit every client immediately to the dependency-free thread pool."""
    result_ids = list(
        ManualTradeResult.objects.filter(batch_id=batch_id, status=ManualTradeResult.STATUS_PENDING)
        .order_by("id")
        .values_list("id", flat=True)
    )
    if not result_ids:
        return _finalize_manual_trade_batch(batch_id)
    dispatcher = _get_manual_trade_dispatcher()
    submitted = 0
    for result_id in result_ids:
        try:
            dispatcher.submit(_execute_manual_trade_result, result_id)
            submitted += 1
        except Exception as exc:
            logger.exception("Could not dispatch manual trade result_id=%s", result_id)
            ManualTradeResult.objects.filter(pk=result_id, status=ManualTradeResult.STATUS_PENDING).update(
                status=ManualTradeResult.STATUS_FAILED,
                reason=f"Immediate dispatch failed: {exc}",
                response_snapshot={"error": str(exc)},
                updated_at=timezone.now(),
            )
    if submitted != len(result_ids):
        _finalize_manual_trade_batch(batch_id)
    return {"status": ManualTradeBatch.STATUS_PROCESSING, "submitted_count": submitted}


def execute_manual_trade_batch(batch_id: int) -> Dict[str, Any]:
    """Synchronous compatibility entry point used by older task invocations."""
    with transaction.atomic():
        batch = ManualTradeBatch.objects.select_for_update().get(pk=batch_id)
        if batch.status not in {ManualTradeBatch.STATUS_QUEUED, ManualTradeBatch.STATUS_PROCESSING}:
            return {"status": "skipped", "message": f"Batch is {batch.status}."}
        batch.status = ManualTradeBatch.STATUS_PROCESSING
        batch.save(update_fields=["status", "updated_at"])
    results = list(
        ManualTradeResult.objects.filter(batch_id=batch_id, status=ManualTradeResult.STATUS_PENDING)
        .order_by("id")
        .values_list("id", flat=True)
    )
    max_workers = max(1, min(len(results), int(getattr(settings, "MANUAL_TRADE_DISPATCH_WORKERS", 32) or 32)))
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(_execute_manual_trade_result, result_id) for result_id in results]
        for future in as_completed(futures):
            future.result()
    return _finalize_manual_trade_batch(batch_id)
