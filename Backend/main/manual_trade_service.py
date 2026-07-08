from __future__ import annotations

import hashlib
from datetime import datetime, timezone as datetime_timezone
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, Optional

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from main.execution_engine import ExecutionRequest, get_execution_engine
from main.broker_instrument_cache import load_upstox_instruments
from main.models import (
    ClientBrokerdetails,
    ClientTradeSetting,
    GroupService,
    ManualTradeBatch,
    ManualTradeResult,
    User,
)
from main.permissions import get_accessible_clients_queryset


ACTION_TO_ORDER = {
    ManualTradeBatch.ACTION_BUY_CE: ("BUY", "CE"),
    ManualTradeBatch.ACTION_BUY_PE: ("BUY", "PE"),
}


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


def _client_name(client) -> str:
    return (
        getattr(client, "fullName", None)
        or " ".join(part for part in [getattr(client, "firstName", None), getattr(client, "lastName", None)] if part)
        or getattr(client, "email", None)
        or f"Client #{getattr(client, 'id', '')}"
    )


def _broker_status(client, trade_setting) -> Dict[str, Any]:
    broker_name = str(getattr(trade_setting, "broker", "") or "").strip()
    if not broker_name:
        return {"ready": False, "broker": "", "reason": "Broker is not selected in client saved script setting."}

    broker_detail = (
        ClientBrokerdetails.objects.select_related("broker_name", "execution_node")
        .filter(client=client, broker_name__broker_name__iexact=broker_name)
        .first()
    )
    if not broker_detail:
        broker_detail = ClientBrokerdetails.objects.select_related("broker_name", "execution_node").filter(client=client).first()
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
    expiry = getattr(setting, "expiry_date", None)
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
    group_service = group_queryset.get(pk=group_service_id)

    settings = _select_one_setting_per_client(_matching_trade_settings(group_service, symbol, actor))
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
        for setting in settings:
            broker_info = _broker_status(setting.client, setting)
            reason = _eligibility_reason(setting, broker_info)
            if not reason:
                reason = _upstox_contract_reason(setting, symbol, strike, ACTION_TO_ORDER[action][1])
            status = ManualTradeResult.STATUS_SKIPPED if reason else ManualTradeResult.STATUS_PENDING
            if reason:
                skipped_count += 1
            else:
                eligible_count += 1
            ManualTradeResult.objects.create(
                batch=batch,
                client=setting.client,
                trade_setting=setting,
                broker=broker_info.get("broker") or setting.broker,
                status=status,
                reason=reason,
                request_snapshot=_result_snapshot(setting, broker_info),
            )

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
    day, month, year, fullyear = _date_parts(setting.expiry_date)
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
        "expiry": setting.expiry_date.date().isoformat() if setting.expiry_date else None,
        "order_type": setting.order_type,
        "product_type": setting.product_type,
        "buffer_percentage": float(setting.buffer_percentage) if setting.buffer_percentage is not None else None,
        "idempotency_key": f"manual:{batch.id}:{result.client_id}",
    }
    return ExecutionRequest(
        LivePrice=batch.strike_price,
        group_service=batch.group_service.group_name,
        trade=setting,
        user=result.client,
        transaction_type=transaction_type,
        symbol=batch.symbol,
        quantity=int(setting.quantity or 0),
        strategy="Manual Trade",
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
    )


def execute_manual_trade_batch(batch_id: int) -> Dict[str, Any]:
    with transaction.atomic():
        batch = ManualTradeBatch.objects.select_for_update().get(pk=batch_id)
        if batch.status not in {ManualTradeBatch.STATUS_QUEUED, ManualTradeBatch.STATUS_PROCESSING}:
            return {"status": "skipped", "message": f"Batch is {batch.status}."}
        batch.status = ManualTradeBatch.STATUS_PROCESSING
        batch.save(update_fields=["status", "updated_at"])

    results = list(
        ManualTradeResult.objects.select_related("batch", "client", "trade_setting", "trade_setting__segment", "trade_setting__sub_segment")
        .filter(batch_id=batch_id, status=ManualTradeResult.STATUS_PENDING)
        .order_by("id")
    )

    for result in results:
        try:
            result.status = ManualTradeResult.STATUS_PROCESSING
            result.reason = "Order is being sent."
            result.save(update_fields=["status", "reason", "updated_at"])

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
            success = broker_status.lower() in {"success", "complete", "completed", "open", "placed", "accepted_by_node", "sent_to_node"}
            result.status = ManualTradeResult.STATUS_SUCCESS if success else ManualTradeResult.STATUS_FAILED
            result.broker_status = broker_status
            result.order_id = data.get("order_id") or data.get("orderid") or data.get("job_id")
            result.reason = data.get("message") or data.get("error") or ("Order sent." if success else "Broker rejected the order.")
            result.response_snapshot = response if isinstance(response, dict) else {"response": str(response)}
            result.save(update_fields=["status", "broker_status", "order_id", "reason", "response_snapshot", "updated_at"])
        except Exception as exc:
            result.status = ManualTradeResult.STATUS_FAILED
            result.reason = str(exc)
            result.response_snapshot = {"error": str(exc)}
            result.save(update_fields=["status", "reason", "response_snapshot", "updated_at"])

    batch = ManualTradeBatch.objects.get(pk=batch_id)
    success_count = batch.results.filter(status=ManualTradeResult.STATUS_SUCCESS).count()
    failed_count = batch.results.filter(status=ManualTradeResult.STATUS_FAILED).count()
    skipped_count = batch.results.filter(status=ManualTradeResult.STATUS_SKIPPED).count()
    pending_count = batch.results.filter(status__in=[ManualTradeResult.STATUS_PENDING, ManualTradeResult.STATUS_PROCESSING]).count()
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
