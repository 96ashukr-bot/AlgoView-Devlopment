from __future__ import annotations

import re

from main.brokers.base import BaseBroker
from main.brokers.utils import build_trade_symbol, common_order_kwargs, get_access_token, get_order_payload
from main.models import Tradeorderhistory
from main.upstock import place_upstox_orders

OPEN_BUY_ORDER_STATUSES = {"complete", "completed", "open", "put order req received", "success"}
CLOSED_TRADE_STATUSES = {"close", "closed"}


def _compact_symbol(value):
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _extract_option_type(value):
    compact = _compact_symbol(value)
    if compact.endswith("CE") or "CE" in compact:
        return "CE"
    if compact.endswith("PE") or "PE" in compact:
        return "PE"
    return ""


def _round_strike_from_signal_price(value):
    try:
        price = float(value)
    except (TypeError, ValueError):
        return ""
    last_two_digits = int(price) % 100
    if last_two_digits > 50:
        return str(int(price) - last_two_digits + 100)
    return str(int(price) - last_two_digits)


def _history_option_type(history):
    contract_symbol = _extract_history_contract_symbol(history)
    option_type = _extract_option_type(contract_symbol)
    if option_type:
        return option_type

    order_params = getattr(history, "order_params", None)
    if isinstance(order_params, dict):
        return _extract_option_type(order_params.get("option_type") or order_params.get("Type") or order_params.get("transaction_type"))
    return ""


def _history_signal_price(history):
    webhook_signal = getattr(history, "webhook_signal", None)
    if isinstance(webhook_signal, dict):
        return webhook_signal.get("signalprice") or webhook_signal.get("price")
    return None


def _extract_history_contract_symbol(history):
    candidates = [getattr(history, "trading_symbol", None)]
    response_data = getattr(history, "response_data", None)

    if isinstance(response_data, dict):
        order_data = response_data.get("data")
        if isinstance(order_data, list):
            candidates.extend(item for item in order_data if isinstance(item, dict))
        elif isinstance(order_data, dict):
            candidates.append(order_data)

    for candidate in candidates:
        if isinstance(candidate, dict):
            for key in ("trading_symbol", "tradingsymbol", "tradingsymbol_name"):
                value = candidate.get(key)
                if _extract_option_type(value):
                    return str(value)
        elif _extract_option_type(candidate):
            return str(candidate)
    return ""


def _upstox_symbol_from_history(history, order):
    history_symbol = _extract_history_contract_symbol(history)
    compact = _compact_symbol(history_symbol)
    fallback = _compact_symbol(build_trade_symbol(order, "upstox"))

    display_match = re.match(r"^([A-Z]+)(\d+)(CE|PE)(\d{2})([A-Z]{3})(\d{2,4})$", compact)
    if display_match:
        return compact

    broker_match = re.match(r"^([A-Z]+)(\d{2})([A-Z]{3})(\d+)(CE|PE)$", compact)
    if broker_match:
        symbol, day, month, strike, option_type = broker_match.groups()
        year = str(order.get("year") or "") or str(order.get("fullyear") or "")[-2:]
        return f"{symbol}{strike}{option_type}{day}{month}{year}"

    option_type = _history_option_type(history)
    strike = _round_strike_from_signal_price(_history_signal_price(history))
    symbol = str(getattr(history, "Index_Symbol", "") or order.get("symbol") or order.get("underlying") or "").upper()
    day = str(order.get("day") or "")
    month = str(order.get("month") or "")
    year = str(order.get("year") or "") or str(order.get("fullyear") or "")[-2:]
    if symbol and strike and option_type and day and month and year:
        return f"{symbol}{strike}{option_type}{day}{month}{year}"

    return fallback


def _history_matches_open_buy(history, option_type):
    order_status = str(getattr(history, "order_status", "") or "").lower()
    trade_status = str(getattr(history, "trade_order_status", "") or "").lower()
    if order_status not in OPEN_BUY_ORDER_STATUSES:
        return False
    if trade_status in CLOSED_TRADE_STATUSES:
        return False

    return _history_option_type(history) == option_type


def _find_matching_open_buy_position(client, order, values, computed_trade_symbol):
    option_type = str(order.get("option_type") or order.get("Type") or "").upper()
    if option_type not in {"CE", "PE"}:
        option_type = _extract_option_type(computed_trade_symbol)
    if option_type not in {"CE", "PE"}:
        return None, ""

    qs = (
        Tradeorderhistory.objects.filter(
            client=client,
            transaction_type__iexact="BUY",
            Index_Symbol__iexact=values["symbol"],
            GroupService=values["group_service"],
        )
        .exclude(order_id__isnull=True)
        .exclude(order_id="")
        .exclude(order_id="0")
        .order_by("-id")
    )

    matches = [history for history in qs if _history_matches_open_buy(history, option_type)]
    if not matches:
        return None, ""

    computed_compact = _compact_symbol(computed_trade_symbol)
    for history in matches:
        close_symbol = _upstox_symbol_from_history(history, order)
        if _compact_symbol(close_symbol) == computed_compact:
            return history, close_symbol

    history = matches[0]
    return history, _upstox_symbol_from_history(history, order)


def _mark_open_position_closed(open_position, response):
    status = str(response.get("data", {}).get("status", "") or "").lower()
    if status in {"completed", "complete", "success", "open", "put order req received"}:
        open_position.trade_order_status = "CLOSE"
        open_position.save(update_fields=["trade_order_status"])


class UpstoxBroker(BaseBroker):
    broker_name = "upstox"
    supports_proxy = True

    def validate_credentials(self, proxy_config=None):
        if not get_access_token(self.broker_details):
            return {"status": "failed", "message": "Missing Upstox access token."}
        return {"status": "success"}

    def place_order(self, payload, proxy_config=None):
        order = get_order_payload(payload)
        values = common_order_kwargs(order)
        trade_symbol = build_trade_symbol(order, self.broker_name)
        open_position = None

        if values["transaction_type"] == "SELL":
            open_position, close_symbol = _find_matching_open_buy_position(
                self.broker_details.client,
                order,
                values,
                trade_symbol,
            )
            if not open_position:
                option_type = str(order.get("option_type") or order.get("Type") or _extract_option_type(trade_symbol) or "").upper()
                return {
                    "data": {
                        "status": "Failed",
                        "message": f"No open BUY {option_type} position found for {values['symbol']} to close.",
                    }
                }
            trade_symbol = close_symbol or trade_symbol
            values["quantity"] = int(open_position.EntryQty or values["quantity"])
            values["Entry_type"] = open_position.Entry_type or values["Entry_type"]
            values["Entry_price"] = open_position.Entry_Price or values["Entry_price"]
            values["EntryQty"] = open_position.EntryQty or values["EntryQty"]

        response = place_upstox_orders(
            values["LivePrice"],
            values["group_service"],
            get_access_token(self.broker_details),
            trade_symbol,
            values["transaction_type"],
            values["symbol"],
            values["quantity"],
            values["strategy"],
            values["ordertype"],
            values["product_type"],
            values["price"],
            self.broker_details.client,
            values["Lots"],
            values["Entry_type"],
            values["Exit_type"],
            values["Entry_price"],
            values["Exit_price"],
            values["EntryQty"],
            values["ExitQty"],
            values["webhook_signal"],
            values["Exchange"],
            values["Segment"],
            values["Index_Symbol"],
            values["triggerPrice"],
            values["trade_order_status"],
            values["history_id"],
            proxy_config=proxy_config,
        )
        if open_position:
            _mark_open_position_closed(open_position, response)
        return response
