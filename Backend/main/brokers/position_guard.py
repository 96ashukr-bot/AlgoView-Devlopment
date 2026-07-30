from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime

from django.db.models import Q

from main.brokers.utils import build_trade_symbol, common_order_kwargs, order_value
from main.models import Tradeorderhistory

OPEN_BUY_ORDER_STATUSES = {"complete", "completed", "success", "traded"}
BROKER_ACCEPTED_OPEN_STATUSES = {"open", "placed", "accepted_by_node", "sent_to_node", "put order req received"}
CLOSED_TRADE_STATUSES = {"close", "closed"}
SUCCESS_CLOSE_STATUSES = {"completed", "complete", "success"}
SUCCESS_EXIT_ORDER_STATUSES = {"complete", "completed", "success", "executed", "traded"}
FAILED_EXIT_ORDER_STATUSES = {"failed", "failure", "rejected", "cancelled", "canceled", "error"}
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

    order_params = getattr(history, "order_params", None)
    if isinstance(order_params, dict):
        stored_strike = (
            order_params.get("strike")
            if order_params.get("strike") not in (None, "")
            else order_params.get("strike_price")
        )
        normalized_strike = _normalized_strike(stored_strike)
        if normalized_strike:
            return normalized_strike

    return round_strike_from_signal_price(_history_signal_price(history))


def _history_expiry_parts(history):
    order_params = getattr(history, "order_params", None)
    expiry = order_params.get("expiry") or order_params.get("expiry_date") if isinstance(order_params, dict) else None
    if expiry:
        try:
            parsed = datetime.strptime(str(expiry)[:10], "%Y-%m-%d")
            return parsed.strftime("%d"), parsed.strftime("%b"), parsed.strftime("%y"), parsed.strftime("%Y")
        except (TypeError, ValueError):
            pass
    if isinstance(order_params, dict):
        return (
            str(order_params.get("day") or ""),
            str(order_params.get("month") or ""),
            str(order_params.get("year") or ""),
            str(order_params.get("fullyear") or ""),
        )
    return "", "", "", ""


def _history_matches_open_buy(history, option_type):
    order_status = str(getattr(history, "order_status", "") or "").lower()
    trade_status = str(getattr(history, "trade_order_status", "") or "").lower()
    has_order_id = bool(getattr(history, "order_id", None))
    if order_status not in OPEN_BUY_ORDER_STATUSES and not _history_is_broker_accepted_open_buy(history):
        return False
    if order_status == "open" and not has_order_id:
        return False
    if order_status in {"open", "pending", "put order req received", "transit"}:
        if history_filled_quantity(history) <= 0:
            return False
    if trade_status in CLOSED_TRADE_STATUSES:
        return False
    return history_option_type(history) == option_type


def history_filled_quantity(history):
    response_data = getattr(history, "response_data", None)
    candidates = []

    def collect(value):
        if isinstance(value, dict):
            for key in ("filled_quantity", "filledshares", "filled_qty"):
                if value.get(key) not in (None, ""):
                    candidates.append(value.get(key))
            for nested in value.values():
                collect(nested)
        elif isinstance(value, list):
            for nested in value:
                collect(nested)

    collect(response_data)
    for value in candidates:
        try:
            quantity = int(float(value))
        except (TypeError, ValueError):
            continue
        if quantity > 0:
            return quantity
    return 0


def _response_indicates_broker_acceptance(value):
    if isinstance(value, dict):
        status = str(value.get("status") or "").strip().lower()
        message = str(value.get("message") or "").strip().lower()
        order_id = value.get("order_id") or value.get("orderid") or value.get("broker_order_id")
        if status in {"ok", "success", "open", "complete", "completed", "placed", "traded"}:
            return True
        if message in {"success", "order placed successfully", "order routed to execution node."}:
            return True
        if order_id and status not in {"failed", "failure", "error", "rejected", "cancelled", "canceled"}:
            return True
        return any(_response_indicates_broker_acceptance(item) for item in value.values())
    if isinstance(value, list):
        return any(_response_indicates_broker_acceptance(item) for item in value)
    return False


def _history_is_broker_accepted_open_buy(history):
    order_status = str(getattr(history, "order_status", "") or "").lower()
    trade_status = str(getattr(history, "trade_order_status", "") or "").lower()
    if order_status not in BROKER_ACCEPTED_OPEN_STATUSES or trade_status not in BROKER_ACCEPTED_OPEN_STATUSES:
        return False
    if not getattr(history, "order_id", None):
        return False
    if history_filled_quantity(history) > 0:
        return True
    response_data = getattr(history, "response_data", None)
    return _response_indicates_broker_acceptance(response_data)


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


def _normalized_strike(value):
    if value in (None, ""):
        return ""
    text = str(value).strip()
    try:
        number = float(text)
    except (TypeError, ValueError):
        return compact_symbol(text)
    if number.is_integer():
        return str(int(number))
    return str(number).rstrip("0").rstrip(".")


def _history_matches_strike(history, strike):
    requested_strike = _normalized_strike(strike)
    if not requested_strike:
        return True
    return _normalized_strike(history_strike(history)) == requested_strike


def _history_is_successful_exit(history):
    order_status = str(getattr(history, "order_status", "") or "").lower()
    trade_status = str(getattr(history, "trade_order_status", "") or "").lower()
    has_order_id = bool(getattr(history, "order_id", None))
    if not has_order_id:
        return False
    # A CLOSE panel state means the exit workflow finished, not necessarily that
    # the broker filled it. Broker failure/rejection must always win.
    if order_status in FAILED_EXIT_ORDER_STATUSES:
        return False
    return trade_status in CLOSED_TRADE_STATUSES or order_status in SUCCESS_EXIT_ORDER_STATUSES


def _matching_exit_exists_after_open(open_history):
    open_id = getattr(open_history, "id", None)
    if not open_id:
        return False
    symbol = getattr(open_history, "Index_Symbol", None) or getattr(open_history, "trading_symbol", None)
    option_type = history_option_type(open_history)
    strike = history_strike(open_history)
    if option_type not in {"CE", "PE"}:
        return False

    exits = (
        Tradeorderhistory.objects.filter(
            client=getattr(open_history, "client", None),
            transaction_type__iexact="SELL",
            id__gt=open_id,
        )
        .exclude(order_id__isnull=True)
        .exclude(order_id="")
        .exclude(order_id="0")
        .order_by("-id")
    )
    group_service = getattr(open_history, "GroupService", None)
    if group_service:
        exits = exits.filter(GroupService=group_service)

    for exit_history in exits:
        if not _history_is_successful_exit(exit_history):
            continue
        if not _history_matches_underlying(exit_history, symbol):
            continue
        if history_option_type(exit_history) != option_type:
            continue
        if not _history_matches_strike(exit_history, strike):
            continue
        return True
    return False


def _target_history_reference(order):
    if not isinstance(order, dict):
        return None
    nested = order.get("order_params") if isinstance(order.get("order_params"), dict) else {}
    webhook = order.get("webhook_signal") if isinstance(order.get("webhook_signal"), dict) else {}
    for source in (order, nested, webhook):
        value = source.get("original_history_id") or source.get("matched_open_history_id")
        if value not in (None, ""):
            return value
    return None


def _find_selected_open_buy_position(client, order):
    reference = _target_history_reference(order)
    if reference in (None, ""):
        return None, False
    identity = Q(history_id=str(reference))
    try:
        identity |= Q(pk=int(reference))
    except (TypeError, ValueError):
        pass
    history = Tradeorderhistory.objects.filter(identity, client=client, transaction_type__iexact="BUY").order_by("-id").first()
    return history, True


def _allocated_exit_quantity(open_history):
    """Return successful SELL quantity explicitly allocated to this BUY row."""
    references = {str(open_history.id)}
    if getattr(open_history, "history_id", None):
        references.add(str(open_history.history_id))
    allocated = 0
    exits = Tradeorderhistory.objects.filter(
        client=open_history.client,
        transaction_type__iexact="SELL",
    ).exclude(order_id__isnull=True).exclude(order_id="").exclude(order_id="0")
    for exit_history in exits.iterator():
        if not _history_is_successful_exit(exit_history):
            continue
        params = exit_history.order_params if isinstance(exit_history.order_params, dict) else {}
        webhook = exit_history.webhook_signal if isinstance(exit_history.webhook_signal, dict) else {}
        reference = params.get("original_history_id") or webhook.get("original_history_id")
        if str(reference or "") not in references:
            continue
        allocated += int(exit_history.ExitQty or params.get("quantity") or 0)
    return allocated


def _confirmed_recorded_exit_quantity(open_history):
    """Return ExitQty only when the BUY row contains evidence of a real exit.

    Older order-placement paths could copy the entry fill quantity into ExitQty
    while leaving the trade open. ExitQty by itself must therefore never make an
    open position unclosable.
    """
    quantity = int(open_history.ExitQty or 0)
    if quantity <= 0:
        return 0

    trade_status = str(open_history.trade_order_status or "").strip().lower()
    exit_status = str(open_history.Exit_status or "").strip().lower()
    has_exit_execution = open_history.Exit_Price is not None

    if trade_status in CLOSED_TRADE_STATUSES and (
        has_exit_execution or exit_status in SUCCESS_EXIT_ORDER_STATUSES
    ):
        return quantity
    if has_exit_execution and exit_status in SUCCESS_EXIT_ORDER_STATUSES:
        return quantity
    return 0


def remaining_open_quantity(open_history):
    recorded_exit = _confirmed_recorded_exit_quantity(open_history)
    return max(0, int(open_history.EntryQty or 0) - max(recorded_exit, _allocated_exit_quantity(open_history)))


def expected_contract_net_quantity(open_history):
    """Expected broker net from independently allocated SaaS BUY rows."""
    total = 0
    candidates = Tradeorderhistory.objects.filter(
        client=open_history.client,
        transaction_type__iexact="BUY",
    ).exclude(order_id__isnull=True).exclude(order_id="").exclude(order_id="0")
    broker = str(getattr(open_history, "broker", "") or "").strip()
    if broker:
        candidates = candidates.filter(broker__iexact=broker)
    open_params = open_history.order_params if isinstance(open_history.order_params, dict) else {}
    expected_product = str(open_params.get("product_type") or open_params.get("product") or "").strip().upper()
    expected_underlying = getattr(open_history, "Index_Symbol", None) or getattr(open_history, "trading_symbol", None)
    expected_type = history_option_type(open_history)
    expected_strike = history_strike(open_history)
    for candidate in candidates.iterator():
        candidate_params = candidate.order_params if isinstance(candidate.order_params, dict) else {}
        candidate_product = str(candidate_params.get("product_type") or candidate_params.get("product") or "").strip().upper()
        if expected_product and candidate_product and candidate_product != expected_product:
            continue
        if not _history_matches_open_buy(candidate, expected_type):
            continue
        if not _history_matches_underlying(candidate, expected_underlying):
            continue
        if not _history_matches_strike(candidate, expected_strike):
            continue
        total += remaining_open_quantity(candidate)
    return total


def find_matching_open_buy_position(client, order, require_exact_strike=False):
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
        )
        .exclude(order_id__isnull=True)
        .exclude(order_id="")
        .exclude(order_id="0")
        .order_by("-id")
    )
    if values["group_service"]:
        qs = qs.filter(GroupService=values["group_service"])
    for history in qs:
        if _history_matches_underlying(history, values["symbol"]) and _history_matches_open_buy(history, option_type):
            return history
    return None


def is_force_broker_squareoff(order):
    if not isinstance(order, dict):
        return False
    nested_order_params = order.get("order_params") if isinstance(order.get("order_params"), dict) else {}
    for source in (order, nested_order_params):
        if source.get("force_broker_squareoff") is True:
            return True
        if str(source.get("order_action") or "").strip().lower() in {"force_kill_switch_exit", "forced_squareoff"}:
            return True
    return False


def prepare_close_order_from_open_position(client, order, broker_name):
    order = deepcopy(order)
    values = common_order_kwargs(order)
    if values["transaction_type"] != "SELL":
        return order, None, None
    option_type = str(order_value(order, "option_type", "Type") or "").upper()
    open_position, selected_explicitly = _find_selected_open_buy_position(client, order)
    if (
        is_force_broker_squareoff(order)
        and not selected_explicitly
        and str(broker_name or "").strip().lower() not in {"groww", "grow"}
    ):
        return order, None, None
    if selected_explicitly and open_position:
        if not _history_matches_open_buy(open_position, history_option_type(open_position)):
            open_position = None
        elif not _history_matches_underlying(open_position, values["symbol"]):
            open_position = None
        elif option_type in {"CE", "PE"} and history_option_type(open_position) != option_type:
            open_position = None
        elif not _history_matches_strike(open_position, order_value(order, "strike", "strike_price")):
            open_position = None
    elif not selected_explicitly:
        open_position = find_matching_open_buy_position(client, order)
    if not open_position:
        return order, None, {
            "data": {
                "status": "Failed",
                "message": (
                    "The selected BUY trade is already closed, has no remaining quantity, or does not match this exit request."
                    if selected_explicitly
                    else f"No open BUY {option_type or 'option'} position found for {values['symbol']} to close."
                ),
            }
        }

    remaining_quantity = remaining_open_quantity(open_position)
    if remaining_quantity <= 0:
        return order, None, {
            "data": {"status": "Failed", "message": "The selected BUY trade has no remaining quantity to close."}
        }
    expected_broker_net = expected_contract_net_quantity(open_position)
    if expected_broker_net < remaining_quantity:
        return order, None, {
            "data": {
                "status": "Failed",
                "message": "The selected exit quantity exceeds the expected broker net position. Refresh positions before retrying.",
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
    day, month, year, fullyear = _history_expiry_parts(open_position)
    if day:
        order["day"] = day
    if month:
        order["month"] = month
    if year:
        order["year"] = year
    if fullyear:
        order["fullyear"] = fullyear
    order["quantity"] = remaining_quantity
    order["Entry_type"] = open_position.Entry_type or values["Entry_type"]
    order["Entry_price"] = open_position.Entry_Price or values["Entry_price"]
    order["EntryQty"] = open_position.EntryQty or values["EntryQty"]
    order["trade_symbol"] = build_trade_symbol(order, broker_name)
    order["trading_symbol"] = order["trade_symbol"]
    order["matched_open_history_id"] = open_position.history_id or open_position.id
    order["expected_broker_net_quantity"] = expected_broker_net
    order["allocated_exit_quantity"] = remaining_quantity
    if selected_explicitly:
        order["original_history_id"] = open_position.history_id or open_position.id
        order["targeted_position_exit"] = True
        order["broker_net_validation_required"] = True
    return order, open_position, None


def mark_open_position_closed(open_position, response):
    if not open_position:
        return
    status = str(response.get("data", {}).get("status", "") or "").lower()
    if status in SUCCESS_CLOSE_STATUSES:
        open_position.trade_order_status = "CLOSE"
        open_position.save(update_fields=["trade_order_status"])
