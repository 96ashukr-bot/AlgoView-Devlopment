from __future__ import annotations

import json
from datetime import datetime
from decimal import Decimal
from typing import Any, Iterable, Optional

from django.core.serializers.json import DjangoJSONEncoder
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from main.brokers.registry import get_broker_adapter
from main.models import ClientBrokerdetails, ClientTradeSetting, Tradeorderhistory
from main.services.proxy_utils import build_requests_proxy_config


SUCCESS_STATUSES = {"complete", "completed", "success", "traded", "filled"}
TERMINAL_FAILURE_STATUSES = {"rejected", "cancelled", "canceled"}
BROKER_STATUS_KEYS = ("status", "order_status", "orderStatus", "orderstatus", "Status")
ORDER_ID_KEYS = (
    "order_id",
    "orderid",
    "orderId",
    "OrderID",
    "brokerOrderId",
    "broker_order_id",
    "RemoteOrderID",
    "ExchOrderID",
    "nestOrderNumber",
    "Nstordno",
    "id",
)
PRICE_KEYS = (
    "average_price",
    "averageprice",
    "averagePrice",
    "AveragePrice",
    "avg_price",
    "avgPrice",
    "avgTradePrice",
    "averageTradePrice",
    "average_trade_price",
    "average_traded_price",
    "average_fill_price",
    "traded_price",
    "tradedPrice",
    "TradedPrice",
    "fill_price",
    "filled_price",
    "executed_price",
)
FALLBACK_PRICE_KEYS = ("price", "Price", "orderPrice", "order_price")
QUANTITY_KEYS = (
    "filled_quantity",
    "filledQuantity",
    "filledQty",
    "Fillshares",
    "filledshares",
    "Qty",
    "qty",
    "quantity",
    "Quantity",
)
EXECUTION_TIME_KEYS = (
    "exchange_timestamp",
    "exchangeTimestamp",
    "exchange_time",
    "exchangeTime",
    "exchtime",
    "trade_timestamp",
    "tradeTimestamp",
    "trade_time",
    "tradeTime",
    "order_timestamp",
    "orderTimestamp",
    "update_timestamp",
    "updateTime",
    "updatetime",
)


def _normalize(value: Any) -> str:
    return str(value or "").strip().lower()


def _to_decimal(value: Any) -> Optional[Decimal]:
    if value in (None, "", "None"):
        return None
    try:
        price = Decimal(str(value))
    except Exception:
        return None
    return price if price > 0 else None


def _to_int(value: Any) -> Optional[int]:
    if value in (None, "", "None"):
        return None
    try:
        quantity = int(float(value))
    except Exception:
        return None
    return quantity if quantity > 0 else None


def _walk_dicts(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        yield value
        for child in value.values():
            yield from _walk_dicts(child)
    elif isinstance(value, list):
        for item in value:
            yield from _walk_dicts(item)


def _record_order_ids(record: dict[str, Any]) -> set[str]:
    values = set()
    for key in ORDER_ID_KEYS:
        value = record.get(key)
        if value not in (None, "", "None"):
            values.add(str(value).strip())
    return values


def _record_status(record: dict[str, Any]) -> str:
    for key in BROKER_STATUS_KEYS:
        value = record.get(key)
        if value not in (None, "", "None"):
            return _normalize(value)
    return ""


def _record_price(record: dict[str, Any]) -> Optional[Decimal]:
    for key in PRICE_KEYS:
        price = _to_decimal(record.get(key))
        if price is not None:
            return price
    if _record_status(record) in SUCCESS_STATUSES:
        for key in FALLBACK_PRICE_KEYS:
            price = _to_decimal(record.get(key))
            if price is not None:
                return price
    return None


def _record_quantity(record: dict[str, Any]) -> Optional[int]:
    for key in QUANTITY_KEYS:
        quantity = _to_int(record.get(key))
        if quantity is not None:
            return quantity
    return None


def _record_execution_time(record: dict[str, Any]) -> Optional[datetime]:
    for key in EXECUTION_TIME_KEYS:
        value = record.get(key)
        if value in (None, "", "None"):
            continue
        parsed = value if isinstance(value, datetime) else parse_datetime(str(value))
        if parsed is None:
            for pattern in (
                "%Y-%m-%d %H:%M:%S",
                "%Y-%m-%dT%H:%M:%S",
                "%d-%b-%Y %H:%M:%S",
            ):
                try:
                    parsed = datetime.strptime(str(value), pattern)
                    break
                except ValueError:
                    continue
        if parsed is None:
            continue
        if timezone.is_naive(parsed):
            parsed = timezone.make_aware(parsed, timezone.get_default_timezone())
        return parsed
    return None


def find_broker_fill(orderbook_response: Any, order_id: Any) -> Optional[dict[str, Any]]:
    expected_order_id = str(order_id or "").strip()
    if not expected_order_id:
        return None

    for record in _walk_dicts(orderbook_response):
        if expected_order_id not in _record_order_ids(record):
            continue
        price = _record_price(record)
        status = _record_status(record)
        quantity = _record_quantity(record)
        return {
            "record": record,
            "price": price,
            "quantity": quantity,
            "status": status,
        }
    return None


def _build_proxy_config(broker_details: ClientBrokerdetails):
    node = getattr(broker_details, "execution_node", None)
    if not node:
        return None
    return build_requests_proxy_config(node)


def _find_trade_setting(trade_order: Tradeorderhistory) -> Optional[ClientTradeSetting]:
    if getattr(trade_order, "trade_setting_id", None):
        return trade_order.trade_setting
    return (
        ClientTradeSetting.objects.filter(
            client=trade_order.client,
            group_service=trade_order.GroupService,
            broker__iexact=str(trade_order.broker or "").strip(),
        )
        .order_by("-id")
        .first()
    )


def _recalculate_sltp_fields(trade_order: Tradeorderhistory, entry_price: Decimal) -> tuple[dict[str, Any], dict[str, Any]]:
    trade_setting = _find_trade_setting(trade_order)
    order_params = dict(trade_order.order_params or {})
    sltp_metadata = dict(trade_order.sltp_metadata or {})
    if not trade_setting:
        return order_params, sltp_metadata

    sl_type = str(getattr(trade_setting, "sl_type", "") or "").strip().upper()
    stop_loss = _to_decimal(getattr(trade_setting, "stop_loss", None))
    target = _to_decimal(getattr(trade_setting, "target", None))
    if sl_type in {"%", "PERCENT", "PERCENTAGE"}:
        sl_mode = "PERCENTAGE"
    elif sl_type in {"POINT", "POINTS"}:
        sl_mode = "POINTS"
    else:
        sl_mode = ""

    if not sl_mode or (stop_loss is None and target is None):
        return order_params, sltp_metadata

    entry_float = float(round(entry_price, 2))
    order_params["entry_reference_price"] = entry_float
    sltp_metadata["entry_option_price"] = entry_float
    sltp_metadata["sl_tp_type"] = sl_mode

    if stop_loss is not None:
        if sl_mode == "PERCENTAGE":
            stop_price = entry_price * (Decimal("1") - (stop_loss / Decimal("100")))
        else:
            stop_price = entry_price - stop_loss
        value = float(round(stop_price, 2))
        order_params["effective_stop_loss_price"] = value
        order_params["calculated_stoploss_price"] = value
        sltp_metadata["calculated_stoploss_price"] = value

    if target is not None:
        if sl_mode == "PERCENTAGE":
            target_price = entry_price * (Decimal("1") + (target / Decimal("100")))
        else:
            target_price = entry_price + target
        value = float(round(target_price, 2))
        order_params["effective_target_price"] = value
        order_params["calculated_target_price"] = value
        sltp_metadata["calculated_target_price"] = value

    return order_params, sltp_metadata


def refresh_trade_fill_from_broker(trade_order: Tradeorderhistory, broker_details: ClientBrokerdetails) -> bool:
    if not trade_order or not broker_details or not trade_order.order_id:
        return False

    current_status = _normalize(trade_order.order_status)
    current_price = _to_decimal(trade_order.Entry_Price if str(trade_order.transaction_type).upper() == "BUY" else trade_order.Exit_Price)
    if current_status in SUCCESS_STATUSES and current_price is not None:
        return False

    try:
        adapter = get_broker_adapter(broker_details)
        orderbook = adapter.get_orderbook(proxy_config=_build_proxy_config(broker_details))
    except Exception:
        return False

    match = find_broker_fill(orderbook, trade_order.order_id)
    if not match:
        return False

    price = match["price"]
    quantity = match.get("quantity")
    status = match.get("status")
    changed = False
    update_fields = []

    if str(trade_order.transaction_type or "").upper() == "SELL" and price is not None:
        if trade_order.Exit_Price != price:
            trade_order.Exit_Price = price
            update_fields.append("Exit_Price")
            changed = True
        if quantity and trade_order.ExitQty != quantity:
            trade_order.ExitQty = quantity
            update_fields.append("ExitQty")
            changed = True
    elif price is not None:
        if trade_order.Entry_Price != price:
            trade_order.Entry_Price = price
            update_fields.append("Entry_Price")
            changed = True
        if quantity and trade_order.EntryQty != quantity:
            trade_order.EntryQty = quantity
            update_fields.append("EntryQty")
            changed = True
        order_params, sltp_metadata = _recalculate_sltp_fields(trade_order, price)
        if order_params != (trade_order.order_params or {}):
            trade_order.order_params = order_params
            update_fields.append("order_params")
            changed = True
        if sltp_metadata != (trade_order.sltp_metadata or {}):
            trade_order.sltp_metadata = sltp_metadata
            update_fields.append("sltp_metadata")
            changed = True

    if status and status != current_status:
        trade_order.order_status = status
        update_fields.append("order_status")
        changed = True

    status_field = "Exit_status" if str(trade_order.transaction_type or "").upper() == "SELL" else "Entry_status"
    if status and _normalize(getattr(trade_order, status_field, None)) != status:
        setattr(trade_order, status_field, status)
        update_fields.append(status_field)
        changed = True

    broker_record = json.loads(json.dumps(match.get("record") or {}, cls=DjangoJSONEncoder))
    if broker_record and trade_order.response_data != broker_record:
        trade_order.response_data = broker_record
        update_fields.append("response_data")
        changed = True

    if status in TERMINAL_FAILURE_STATUSES:
        failure_reason = str(
            broker_record.get("status_message")
            or broker_record.get("status_message_raw")
            or f"Broker order was {status}."
        )
        if trade_order.failure_reason != failure_reason:
            trade_order.failure_reason = failure_reason
            update_fields.append("failure_reason")
            changed = True
    elif status in SUCCESS_STATUSES and trade_order.failure_reason:
        trade_order.failure_reason = None
        update_fields.append("failure_reason")
        changed = True

    if changed:
        trade_order.save(update_fields=list(dict.fromkeys(update_fields)))
    if status in SUCCESS_STATUSES:
        from main.services.trade_limit import complete_successful_buy_slot

        order_params = trade_order.order_params if isinstance(trade_order.order_params, dict) else {}
        complete_successful_buy_slot(order_params.get("trade_limit_reservation_key"))
    elif status in TERMINAL_FAILURE_STATUSES:
        from main.services.trade_limit import release_successful_buy_slot

        order_params = trade_order.order_params if isinstance(trade_order.order_params, dict) else {}
        release_successful_buy_slot(order_params.get("trade_limit_reservation_key"))
    return changed
