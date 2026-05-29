from __future__ import annotations

import re
from copy import deepcopy

from main.brokers.utils import build_trade_symbol, common_order_kwargs, order_value
from main.models import Tradeorderhistory

OPEN_BUY_ORDER_STATUSES = {"complete", "completed", "success"}
CLOSED_TRADE_STATUSES = {"close", "closed"}
SUCCESS_CLOSE_STATUSES = {"completed", "complete", "success", "open", "put order req received"}
KNOWN_UNDERLYINGS = ("MIDCPNIFTY", "BANKNIFTY", "FINNIFTY", "SENSEX", "BANKEX", "NIFTY")


def compact_symbol(value):
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def extract_option_type(value):
    compact = compact_symbol(value)
    if compact.endswith("CE") or "CE" in compact:
        return "CE"
    if compact.endswith("PE") or "PE" in compact:
        return "PE"
    return ""


def extract_underlying(value):
    compact = compact_symbol(value)
    for underlying in KNOWN_UNDERLYINGS:
        if compact.startswith(underlying):
            return underlying
    return compact


def round_strike_from_signal_price(value):
    try:
        price = float(value)
    except (TypeError, ValueError):
        return ""
    last_two_digits = int(price) % 100
    if last_two_digits > 50:
        return str(int(price) - last_two_digits + 100)
    return str(int(price) - last_two_digits)


def _extract_history_contract_symbol(history):
    candidates = [getattr(history, "trading_symbol", None), getattr(history, "Index_Symbol", None)]
    response_data = getattr(history, "response_data", None)

    if isinstance(response_data, dict):
        order_data = response_data.get("data")
        if isinstance(order_data, list):
            candidates.extend(item for item in order_data if isinstance(item, dict))
        elif isinstance(order_data, dict):
            candidates.append(order_data)

    for candidate in candidates:
        if isinstance(candidate, dict):
            for key in ("trading_symbol", "tradingsymbol", "tradingsymbol_name", "symbol"):
                value = candidate.get(key)
                if extract_option_type(value):
                    return str(value)
        elif extract_option_type(candidate):
            return str(candidate)
    return ""


def _option_type_from_webhook(history):
    webhook_signal = getattr(history, "webhook_signal", None)
    if not isinstance(webhook_signal, dict):
        return ""
    order_type = str(webhook_signal.get("ordertype") or "").upper()
    if order_type == "BUY-O":
        return "CE"
    if order_type == "SELL-O":
        return "PE"
    return ""


def history_option_type(history):
    contract_symbol = _extract_history_contract_symbol(history)
    option_type = extract_option_type(contract_symbol)
    if option_type:
        return option_type

    order_params = getattr(history, "order_params", None)
    if isinstance(order_params, dict):
        option_type = extract_option_type(
            order_params.get("option_type")
            or order_params.get("Type")
            or order_params.get("transaction_type")
        )
        if option_type:
            return option_type
    return _option_type_from_webhook(history)


def _history_signal_price(history):
    webhook_signal = getattr(history, "webhook_signal", None)
    if isinstance(webhook_signal, dict):
        return webhook_signal.get("signalprice") or webhook_signal.get("price")
    return None


def history_strike(history):
    contract_symbol = compact_symbol(_extract_history_contract_symbol(history))
    underlying = extract_underlying(contract_symbol)
    if underlying and contract_symbol.startswith(underlying):
        contract_body = contract_symbol[len(underlying):]
    else:
        contract_body = contract_symbol

    option_match = re.search(r"(CE|PE)", contract_body)
    if option_match:
        contract_body = contract_body[: option_match.start()]

    expiry_prefixed_patterns = (
        r"^\d{2}[A-Z]{3}\d{2}(\d{4,6})$",
        r"^\d{2}[A-Z]{3}\d{4}(\d{4,6})$",
        r"^\d{2}[A-Z]{3}(\d{4,6})$",
        r"^[A-Z]{3}\d{2}(\d{4,6})$",
        r"^[A-Z]{3}\d{4}(\d{4,6})$",
    )
    for pattern in expiry_prefixed_patterns:
        match = re.match(pattern, contract_body)
        if match:
            return match.group(1)

    digit_groups = re.findall(r"\d+", contract_body)
    for group in reversed(digit_groups):
        if 4 <= len(group) <= 6:
            return group
        if len(group) > 6:
            return group[-5:]
    return round_strike_from_signal_price(_history_signal_price(history))


def _history_matches_open_buy(history, option_type):
    order_status = str(getattr(history, "order_status", "") or "").lower()
    trade_status = str(getattr(history, "trade_order_status", "") or "").lower()
    if order_status not in OPEN_BUY_ORDER_STATUSES:
        return False
    if trade_status in CLOSED_TRADE_STATUSES:
        return False
    return history_option_type(history) == option_type


def _history_matches_underlying(history, symbol):
    expected_underlying = extract_underlying(symbol)
    if not expected_underlying:
        return True

    candidates = [
        _extract_history_contract_symbol(history),
        getattr(history, "Index_Symbol", None),
        getattr(history, "trading_symbol", None),
    ]
    for candidate in candidates:
        if extract_underlying(candidate) == expected_underlying:
            return True
    return False


def find_matching_open_buy_position(client, order):
    values = common_order_kwargs(order)
    option_type = str(order_value(order, "option_type", "Type") or "").upper()
    if option_type not in {"CE", "PE"}:
        option_type = extract_option_type(build_trade_symbol(order, "upstox"))
    if option_type not in {"CE", "PE"}:
        return None

    qs = (
        Tradeorderhistory.objects.filter(
            client=client,
            transaction_type__iexact="BUY",
            GroupService=values["group_service"],
        )
        .exclude(order_id__isnull=True)
        .exclude(order_id="")
        .exclude(order_id="0")
        .order_by("-id")
    )
    for history in qs:
        if _history_matches_underlying(history, values["symbol"]) and _history_matches_open_buy(history, option_type):
            return history
    return None


def prepare_close_order_from_open_position(client, order, broker_name):
    order = deepcopy(order)
    values = common_order_kwargs(order)
    if values["transaction_type"] != "SELL":
        return order, None, None

    option_type = str(order_value(order, "option_type", "Type") or "").upper()
    open_position = find_matching_open_buy_position(client, order)
    if not open_position:
        return order, None, {
            "data": {
                "status": "Failed",
                "message": f"No open BUY {option_type or 'option'} position found for {values['symbol']} to close.",
            }
        }

    strike = history_strike(open_position)
    option_type = history_option_type(open_position) or option_type
    if strike:
        order["strike"] = strike
        order["strike_price"] = strike
    if option_type:
        order["option_type"] = option_type
        order["Type"] = option_type
    order["quantity"] = int(open_position.EntryQty or values["quantity"])
    order["Entry_type"] = open_position.Entry_type or values["Entry_type"]
    order["Entry_price"] = open_position.Entry_Price or values["Entry_price"]
    order["EntryQty"] = open_position.EntryQty or values["EntryQty"]
    order["trade_symbol"] = build_trade_symbol(order, broker_name)
    order["trading_symbol"] = order["trade_symbol"]
    return order, open_position, None


def mark_open_position_closed(open_position, response):
    if not open_position:
        return
    status = str(response.get("data", {}).get("status", "") or "").lower()
    if status in SUCCESS_CLOSE_STATUSES:
        open_position.trade_order_status = "CLOSE"
        open_position.save(update_fields=["trade_order_status"])
