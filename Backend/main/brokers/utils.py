from __future__ import annotations

from datetime import datetime
from typing import Any


def get_order_payload(payload: dict[str, Any]) -> dict[str, Any]:
    return payload.get("order", payload)


def get_access_token(broker_details) -> str | None:
    if hasattr(broker_details, "get_access_token_secure"):
        token = broker_details.get_access_token_secure()
        if token:
            return token
    return getattr(broker_details, "access_token", None)


def get_api_secret(broker_details) -> str | None:
    if hasattr(broker_details, "get_broker_api_secret"):
        secret = broker_details.get_broker_api_secret()
        if secret:
            return secret
    return getattr(broker_details, "broker_API_SKEY", None)


def order_value(order: dict[str, Any], *keys: str, default: Any = None) -> Any:
    for key in keys:
        value = order.get(key)
        if value not in (None, ""):
            return value
    return default


def int_value(value: Any, default: int = 0) -> int:
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def upper_value(value: Any, default: str = "") -> str:
    return str(value or default).upper()


def common_order_kwargs(order: dict[str, Any]) -> dict[str, Any]:
    return {
        "LivePrice": order.get("LivePrice"),
        "group_service": order.get("group_service"),
        "transaction_type": upper_value(order.get("transaction_type")),
        "symbol": upper_value(order_value(order, "symbol", "underlying", "Index_Symbol")),
        "quantity": int_value(order.get("quantity")),
        "strategy": order.get("strategy"),
        "ordertype": upper_value(order_value(order, "order_type", "ordertype"), "LIMIT"),
        "product_type": upper_value(order_value(order, "product_type", "product"), "INTRADAY"),
        "price": order.get("price"),
        "user": order.get("user"),
        "Lots": order.get("Lots") or 1,
        "trade_order_status": order.get("trade_order_status"),
        "Entry_type": order.get("Entry_type"),
        "Exit_type": order.get("Exit_type"),
        "Entry_price": order.get("Entry_price"),
        "Exit_price": order.get("Exit_price"),
        "EntryQty": order.get("EntryQty"),
        "ExitQty": order.get("ExitQty"),
        "webhook_signal": order.get("webhook_signal"),
        "Exchange": upper_value(order_value(order, "Exchange", "exchange"), "NFO"),
        "Segment": order.get("Segment"),
        "Index_Symbol": order.get("Index_Symbol"),
        "triggerPrice": order_value(order, "triggerPrice", "trigger_price"),
        "history_id": order_value(order, "history_id", "request_id", "idempotency_key"),
    }


def _strike_component(order: dict[str, Any], decimal: bool = False) -> str:
    strike = order_value(order, "strike", "strike_price")
    if strike in (None, ""):
        return ""
    try:
        return f"{float(strike):.2f}" if decimal else str(int(float(strike)))
    except (TypeError, ValueError):
        return str(strike)


def expiry_parts(order: dict[str, Any]) -> tuple[str, str, str, str]:
    return (
        str(order.get("day") or ""),
        str(order.get("month") or ""),
        str(order.get("year") or ""),
        str(order.get("fullyear") or order.get("year") or ""),
    )


def build_trade_symbol(order: dict[str, Any], broker_name: str) -> str:
    explicit = order_value(order, "trade_symbol", "trading_symbol")
    if explicit:
        return str(explicit)

    symbol = upper_value(order_value(order, "symbol", "underlying", "Index_Symbol"))
    option_type = upper_value(order_value(order, "option_type", "Type"))
    day, month, year, fullyear = expiry_parts(order)

    if broker_name == "dhan":
        return f"{symbol}{month}{fullyear}{_strike_component(order)}{option_type}"
    if broker_name == "5paisa":
        return f"{symbol}{day}{month}{fullyear}{option_type}{_strike_component(order, decimal=True)}"
    if broker_name == "upstox":
        return f"{symbol}{_strike_component(order)}{option_type}{day}{month}{year}"
    if broker_name == "zerodha":
        return f"{symbol}{year}{month}{_strike_component(order)}{option_type}"
    if broker_name == "fyers":
        return f"{symbol}{year}{month}{day}{_strike_component(order)}{option_type}"
    return str(order_value(order, "symbol", "underlying", default=""))


def build_dhan_expiry_date(order: dict[str, Any]) -> str:
    explicit = order.get("expiry_date")
    if explicit:
        return str(explicit)
    day, month, _year, fullyear = expiry_parts(order)
    if not (day and month and fullyear):
        return ""
    try:
        month_number = datetime.strptime(month[:3], "%b").month
        return f"{fullyear}-{month_number:02d}-{int(day):02d}"
    except (TypeError, ValueError):
        return ""
