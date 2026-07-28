from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Any, Dict, Iterable, Optional

from django.db import transaction
from django.db.models import Q, QuerySet
from django.utils import timezone
from django.utils.dateparse import parse_date

from main.models import Tradeorderhistory


MIS_PRODUCT_VALUES = {"MIS", "INTRADAY", "I"}
SUCCESS_ENTRY_STATUSES = {"complete", "completed", "success", "traded", "filled", "executed", "open"}
FAILED_STATUSES = {"failed", "failure", "rejected", "reject", "error", "errors", "unauthorized", "cancelled", "canceled", "skipped"}
MARKET_CLOSE_TIME = time(15, 30)
ATTENTION_STATUS = "EOD_MIS_CLOSE_PRICE_MISSING"


@dataclass
class EodMisClosureResult:
    scanned: int = 0
    closed: int = 0
    skipped: int = 0
    attention_required: int = 0
    failed_unconfirmed: int = 0

    def to_dict(self) -> Dict[str, int]:
        return {
            "scanned": self.scanned,
            "closed": self.closed,
            "skipped": self.skipped,
            "attention_required": self.attention_required,
            "failed_unconfirmed": self.failed_unconfirmed,
        }


def _normalize_status(value: Any) -> str:
    return str(value or "").strip().lower()


def _normalize_product(value: Any) -> str:
    return str(value or "").strip().upper()


def _get_mapping(*values: Any) -> Dict[str, Any]:
    for value in values:
        if isinstance(value, dict):
            return value
    return {}


def _extract_product_type(history: Tradeorderhistory) -> str:
    order_params = _get_mapping(history.order_params)
    metadata = _get_mapping(getattr(history, "sltp_metadata", None))
    for container in (order_params, metadata):
        for key in ("product_type", "product", "productType", "order_product_type"):
            product = _normalize_product(container.get(key))
            if product:
                return product
    return ""


def _extract_expiry_date(history: Tradeorderhistory):
    order_params = _get_mapping(history.order_params)
    metadata = _get_mapping(getattr(history, "sltp_metadata", None))
    for container in (order_params, metadata):
        value = container.get("expiry") or container.get("expiry_date")
        if not value:
            continue
        if hasattr(value, "date"):
            return value.date()
        parsed = parse_date(str(value).split("T", 1)[0])
        if parsed:
            return parsed
        for date_format in ("%d%b%Y", "%d%b%y"):
            try:
                return datetime.strptime(str(value).upper(), date_format).date()
            except ValueError:
                continue
    return None


def _decimal_or_none(value: Any) -> Optional[Decimal]:
    if value in (None, ""):
        return None
    try:
        decimal_value = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        return None
    if decimal_value <= 0:
        return None
    return decimal_value.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _nested_values(container: Dict[str, Any], keys: Iterable[str]) -> Iterable[Any]:
    for key in keys:
        if key in container:
            yield container.get(key)
    for value in container.values():
        if isinstance(value, dict):
            yield from _nested_values(value, keys)


def resolve_eod_exit_price(history: Tradeorderhistory) -> tuple[Optional[Decimal], Optional[str]]:
    order_params = _get_mapping(history.order_params)
    metadata = _get_mapping(getattr(history, "sltp_metadata", None))
    response_data = _get_mapping(history.response_data)

    candidates = [
        ("order_params.eod_close_price", order_params.get("eod_close_price")),
        ("order_params.closing_price", order_params.get("closing_price")),
        ("sltp_metadata.eod_close_price", metadata.get("eod_close_price")),
        ("sltp_metadata.closing_price", metadata.get("closing_price")),
        ("LivePrice", history.LivePrice),
        ("order_params.ltp", order_params.get("ltp")),
        ("sltp_metadata.current_ltp", metadata.get("current_ltp")),
        ("sltp_metadata.last_ltp", metadata.get("last_ltp")),
    ]
    response_price_keys = (
        "closing_price",
        "close_price",
        "ltp",
        "last_price",
        "average_price",
        "averagePrice",
        "avg_price",
        "filled_price",
        "fill_price",
        "price",
    )
    candidates.extend(("response_data.price", value) for value in _nested_values(response_data, response_price_keys))

    for source, value in candidates:
        price = _decimal_or_none(value)
        if price is not None:
            return price, source
    return None, None


def _market_close_datetime_for(history_date, now=None):
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    close_dt = datetime.combine(history_date or local_now.date(), MARKET_CLOSE_TIME)
    if timezone.is_naive(close_dt):
        close_dt = timezone.make_aware(close_dt, timezone.get_current_timezone())
    return close_dt


def _is_due_for_eod_close(history: Tradeorderhistory, now=None) -> bool:
    now = now or timezone.now()
    local_now = timezone.localtime(now)
    history_date = history.date or local_now.date()
    if history_date < local_now.date():
        return True
    return history_date == local_now.date() and local_now.time() >= MARKET_CLOSE_TIME


def _base_queryset() -> QuerySet:
    active_status_filter = (
        Q(trade_order_status__iregex=r"^(open|entry|buy|active|pending|placed|transit|partial|partially_filled|processing)$")
        | Q(order_status__iregex=r"^(open|complete|completed|executed|filled|traded|success|placed|transit|pending|partial|partially_filled)$")
    )
    failure_filter = (
        Q(order_status__iregex=r"(failed|failure|reject|error|unauthorized|cancel|skipped)")
        | Q(trade_order_status__iregex=r"(failed|failure|reject|error|unauthorized|cancel|skipped)")
        | (Q(failure_reason__isnull=False) & ~Q(failure_reason=""))
    )
    return Tradeorderhistory.objects.select_related("client").filter(
        active_status_filter,
        Exit_Price__isnull=True,
        Exit_type__isnull=True,
    ).exclude(
        trade_order_status__iregex=r"^(close|closed|exit|exited|squareoff|squared_off)$",
    ).exclude(failure_filter)


def _eligible_for_eod_close(history: Tradeorderhistory, now=None) -> bool:
    if not str(history.transaction_type or "").strip().upper().startswith("BUY"):
        return False
    order_status = _normalize_status(history.order_status)
    trade_status = _normalize_status(history.trade_order_status)
    if order_status in FAILED_STATUSES or trade_status in FAILED_STATUSES:
        return False
    if not ({order_status, trade_status} & SUCCESS_ENTRY_STATUSES):
        return False
    product = _normalize_product(_extract_product_type(history))
    if product in MIS_PRODUCT_VALUES and _is_due_for_eod_close(history, now=now):
        return True
    expiry_date = _extract_expiry_date(history)
    if not expiry_date:
        return False
    local_now = timezone.localtime(now or timezone.now())
    return expiry_date < local_now.date() or (
        expiry_date == local_now.date()
        and local_now.time() >= MARKET_CLOSE_TIME
    )


def _is_stale_unconfirmed(history: Tradeorderhistory, now=None) -> bool:
    order_status = _normalize_status(history.order_status)
    trade_status = _normalize_status(history.trade_order_status)
    is_pending = order_status in {"pending", "processing", "transit"} or trade_status in {
        "pending", "processing", "transit",
    }
    has_execution_identity = (
        str(history.order_id or "").strip() not in {"", "0"}
        and _decimal_or_none(history.Entry_Price) is not None
        and int(history.EntryQty or 0) > 0
    )
    if not is_pending and has_execution_identity:
        return False
    if _normalize_product(_extract_product_type(history)) in MIS_PRODUCT_VALUES:
        return _is_due_for_eod_close(history, now=now)
    expiry_date = _extract_expiry_date(history)
    if not expiry_date:
        return False
    local_now = timezone.localtime(now or timezone.now())
    return expiry_date <= local_now.date() and (
        expiry_date < local_now.date()
        or local_now.time() >= MARKET_CLOSE_TIME
    )


def _mark_unconfirmed_failed(history: Tradeorderhistory):
    reason = "Order was never confirmed as executed and is past its trading session or contract expiry."
    with transaction.atomic():
        locked = Tradeorderhistory.objects.select_for_update().get(pk=history.pk)
        if _normalize_status(locked.trade_order_status) in {"close", "closed"}:
            return False
        locked.trade_order_status = "Failed"
        locked.order_status = "Failed"
        locked.failure_reason = reason
        locked.Entry_status = locked.Entry_status or "Failed"
        locked.sltp_status = "FAILED"
        locked.sltp_last_action = "STALE_UNCONFIRMED_ORDER"
        locked.sltp_last_failure_reason = reason
        locked.sltp_manual_attention = False
        locked.sltp_last_checked_at = timezone.now()
        locked.save(update_fields=[
            "trade_order_status",
            "order_status",
            "failure_reason",
            "Entry_status",
            "sltp_status",
            "sltp_last_action",
            "sltp_last_failure_reason",
            "sltp_manual_attention",
            "sltp_last_checked_at",
        ])
    return True


def close_expired_mis_trades(*, company_id=None, client_ids=None, trade_id=None, now=None, dry_run=False) -> Dict[str, int]:
    queryset = _base_queryset()
    # AlgoView is a single-company application. ``company_id`` is accepted for
    # call compatibility with the SaaS watcher but must not reference SaaS-only
    # tenant fields on the AlgoView user model.
    if client_ids is not None:
        queryset = queryset.filter(client_id__in=client_ids)
    if trade_id:
        queryset = queryset.filter(pk=trade_id)

    result = EodMisClosureResult()
    for history in queryset.order_by("id"):
        result.scanned += 1
        if _is_stale_unconfirmed(history, now=now):
            result.failed_unconfirmed += 1
            if not dry_run:
                _mark_unconfirmed_failed(history)
            continue
        if not _eligible_for_eod_close(history, now=now):
            result.skipped += 1
            continue

        exit_price, price_source = resolve_eod_exit_price(history)
        if exit_price is None:
            result.attention_required += 1
            if not dry_run:
                history.sltp_status = ATTENTION_STATUS
                history.sltp_last_action = "EOD_MIS_CLOSE_SKIPPED"
                history.sltp_last_failure_reason = "MIS trade is past market close but no last/closing price is available."
                history.sltp_manual_attention = True
                history.sltp_last_checked_at = timezone.now()
                history.save(update_fields=[
                    "sltp_status",
                    "sltp_last_action",
                    "sltp_last_failure_reason",
                    "sltp_manual_attention",
                    "sltp_last_checked_at",
                ])
            continue

        result.closed += 1
        if dry_run:
            continue

        with transaction.atomic():
            locked = Tradeorderhistory.objects.select_for_update().get(pk=history.pk)
            if locked.Exit_Price is not None or _normalize_status(locked.trade_order_status) == "close":
                continue
            order_params = dict(locked.order_params or {})
            product = _normalize_product(_extract_product_type(locked))
            expiry_date = _extract_expiry_date(locked)
            close_reason = (
                "MIS product auto-square-off assumed after market close."
                if product in MIS_PRODUCT_VALUES
                else "Option contract reached expiry and can no longer remain active."
            )
            order_params["eod_mis_auto_close"] = {
                "source": "system_stale_active_reconciliation",
                "reason": close_reason,
                "exit_price": str(exit_price),
                "exit_price_source": price_source,
                "closed_at": timezone.localtime(timezone.now()).isoformat(),
            }
            locked.Exit_Price = exit_price
            locked.ExitQty = locked.EntryQty
            locked.Exit_type = locked.Exit_type or "LX"
            locked.Exit_status = locked.Exit_status or "AUTO_CLOSED_EOD_MIS"
            close_date = expiry_date if product not in MIS_PRODUCT_VALUES and expiry_date else locked.date
            locked.SignalExit_time = locked.SignalExit_time or _market_close_datetime_for(close_date, now=now)
            locked.LivePrice = exit_price
            locked.trade_order_status = "CLOSE"
            entry_price = Decimal(str(locked.Entry_Price or 0))
            quantity = int(locked.EntryQty or 0)
            if quantity > 0:
                locked.Total = (
                    (entry_price - exit_price) * quantity
                    if str(locked.Entry_type or "").strip().upper() in {"SELL", "SHORT"}
                    else (exit_price - entry_price) * quantity
                )
            locked.sltp_status = "CLOSED"
            locked.sltp_last_action = "EOD_MIS_AUTO_CLOSE"
            locked.sltp_last_failure_reason = None
            locked.sltp_manual_attention = False
            locked.sltp_last_checked_at = timezone.now()
            locked.order_params = order_params
            locked.save(update_fields=[
                "Exit_Price",
                "ExitQty",
                "Exit_type",
                "Exit_status",
                "SignalExit_time",
                "LivePrice",
                "trade_order_status",
                "Total",
                "sltp_status",
                "sltp_last_action",
                "sltp_last_failure_reason",
                "sltp_manual_attention",
                "sltp_last_checked_at",
                "order_params",
            ])

    return result.to_dict()
