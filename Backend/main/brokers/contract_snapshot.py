from __future__ import annotations

from copy import deepcopy
from datetime import date, datetime
from decimal import Decimal

from django.utils import timezone


SNAPSHOT_KEY = "broker_contract_snapshot"
SCHEMA_VERSION = 1


def _json_value(value):
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    if isinstance(value, Decimal):
        return float(value)
    return value


def _walk(value):
    if isinstance(value, dict):
        yield value
        for nested in value.values():
            yield from _walk(nested)
    elif isinstance(value, (list, tuple)):
        for nested in value:
            yield from _walk(nested)


def canonical_contract_fields(*sources):
    mappings = [mapping for source in sources for mapping in _walk(source)]

    def first(*keys):
        for key in keys:
            for mapping in mappings:
                lowered = {str(name).lower(): value for name, value in mapping.items()}
                value = mapping.get(key)
                if value in (None, "", "None"):
                    value = lowered.get(str(key).lower())
                if value not in (None, "", "None"):
                    return value
        return None

    return {
        "original_broker_trading_symbol": first(
            "original_broker_trading_symbol", "resolved_trading_symbol", "tradingsymbol",
            "tradingSymbol", "trading_symbol", "Tsym", "ScripName", "symbol",
        ),
        "original_broker_instrument_key": first(
            "original_broker_instrument_key", "instrument_key", "instrument_token",
            "instrumentToken", "instrumentId", "instrument_id",
        ),
        "original_broker_security_id": first("original_broker_security_id", "security_id", "securityId"),
        "original_broker_symbol_token": first(
            "original_broker_symbol_token", "symboltoken", "symbol_token", "token", "Token",
            "ScripCode", "scrip_code",
        ),
        "original_broker_product_type": first(
            "original_broker_product_type", "producttype", "productType", "product_type", "product", "Pcode",
        ),
        "original_broker_exchange": first(
            "original_broker_exchange", "exchange", "Exchange", "exchangeSegment", "exchange_segment", "exch_seg",
        ),
        "original_broker_segment": first("original_broker_segment", "segment", "Segment", "segment_type"),
        "original_broker_exchange_type": first(
            "original_broker_exchange_type", "exchange_type", "ExchangeType", "ExchType",
        ),
        "original_broker_quantity": first(
            "original_broker_quantity", "filled_quantity", "filledQuantity", "filledQty",
            "filledshares", "quantity", "qty", "Qty",
        ),
    }


def _instrument_id(broker_name, fields):
    broker = str(broker_name or "").strip().lower()
    if broker in {"angel one", "angelone", "angle one"}:
        return fields.get("original_broker_symbol_token") or fields.get("original_broker_instrument_key")
    if broker == "dhan":
        return fields.get("original_broker_security_id")
    if broker == "upstox":
        return fields.get("original_broker_instrument_key")
    if broker in {"alice blue", "aliceblue"}:
        return fields.get("original_broker_instrument_key") or fields.get("original_broker_symbol_token")
    if broker in {"5paisa", "five paisa", "fivepaisa"}:
        return fields.get("original_broker_symbol_token") or fields.get("original_broker_instrument_key")
    return fields.get("original_broker_instrument_key") or fields.get("original_broker_trading_symbol")


def build_snapshot(*, broker_name, fields, underlying, expiry, strike, option_type, buy_order_id, filled_quantity):
    fields = fields if isinstance(fields, dict) else {}
    snapshot = {
        "schema_version": SCHEMA_VERSION,
        "broker": str(broker_name or "").strip(),
        "broker_trading_symbol": fields.get("original_broker_trading_symbol"),
        "broker_instrument_id": _instrument_id(broker_name, fields),
        "broker_exchange": fields.get("original_broker_exchange"),
        "broker_segment": fields.get("original_broker_segment"),
        "broker_exchange_type": fields.get("original_broker_exchange_type"),
        "broker_product_type": fields.get("original_broker_product_type"),
        "filled_quantity": filled_quantity or fields.get("original_broker_quantity"),
        "underlying": underlying,
        "expiry": expiry,
        "strike": strike,
        "option_type": str(option_type or "").strip().upper() or None,
        "buy_order_id": buy_order_id,
        "created_at": timezone.now().isoformat(),
    }
    return {key: _json_value(value) for key, value in snapshot.items()}


def valid_snapshot(value):
    if not isinstance(value, dict) or value.get("schema_version") != SCHEMA_VERSION:
        return False
    required = (
        "broker_trading_symbol", "broker_instrument_id", "broker_exchange",
        "broker_product_type", "filled_quantity", "buy_order_id",
    )
    if any(value.get(key) in (None, "", "None") for key in required):
        return False
    try:
        return int(float(value["filled_quantity"])) > 0
    except (TypeError, ValueError):
        return False


def immutable_snapshot(*sources):
    for source in sources:
        if isinstance(source, dict) and valid_snapshot(source.get(SNAPSHOT_KEY)):
            return deepcopy(source[SNAPSHOT_KEY])
    return None


def snapshot_exit_fields(snapshot):
    if not valid_snapshot(snapshot):
        return {}
    return {
        SNAPSHOT_KEY: deepcopy(snapshot),
        "original_broker_trading_symbol": snapshot.get("broker_trading_symbol"),
        "original_broker_instrument_key": snapshot.get("broker_instrument_id"),
        "original_broker_security_id": snapshot.get("broker_instrument_id"),
        "original_broker_symbol_token": snapshot.get("broker_instrument_id"),
        "original_broker_product_type": snapshot.get("broker_product_type"),
        "original_broker_exchange": snapshot.get("broker_exchange"),
        "original_broker_segment": snapshot.get("broker_segment"),
        "original_broker_exchange_type": snapshot.get("broker_exchange_type"),
        "original_broker_quantity": snapshot.get("filled_quantity"),
    }
