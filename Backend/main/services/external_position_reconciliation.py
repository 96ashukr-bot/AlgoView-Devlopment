from __future__ import annotations

import json
import logging
import re
import time
from decimal import Decimal
from typing import Any, Iterable

from django.core.serializers.json import DjangoJSONEncoder
from django.db import transaction
from django.utils import timezone

from main.broker_registry import normalize_broker_name
from main.brokers.registry import get_broker_adapter
from main.models import ClientBrokerdetails, Tradeorderhistory
from main.services.broker_fill_reconciliation import (
    SUCCESS_STATUSES,
    _record_execution_time,
    _record_order_ids,
    _record_price,
    _record_quantity,
    _record_status,
    _walk_dicts,
)
from main.services.proxy_utils import build_requests_proxy_config


logger = logging.getLogger("main")
SELL_VALUES = {"sell", "s", "-1"}
SYMBOL_KEYS = ("tradingsymbol", "tradingSymbol", "trading_symbol", "symbol", "symbolName")
PRODUCT_KEYS = ("producttype", "productType", "product", "product_type")
TRANSACTION_KEYS = ("transactiontype", "transactionType", "transaction_type", "side")
NET_QUANTITY_KEYS = ("netqty", "netQty", "net_quantity", "netQuantity", "quantity")
PRODUCT_ALIASES = {
    "MIS": "INTRADAY",
    "I": "INTRADAY",
    "INTRADAY": "INTRADAY",
    "CNC": "DELIVERY",
    "C": "DELIVERY",
    "DELIVERY": "DELIVERY",
    "LONGTERM": "DELIVERY",
    "NRML": "CARRYFORWARD",
    "NORMAL": "CARRYFORWARD",
    "CARRYFORWARD": "CARRYFORWARD",
}
TRANSIENT_BROKER_MARKERS = (
    "access denied because of exceeding access rate",
    "access rate",
    "rate limit",
    "rate-limit",
    "too many requests",
    "429",
    "temporarily unavailable",
    "timeout",
    "timed out",
    "connection reset",
)


def _compact_symbol(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _first(record: dict[str, Any], keys: Iterable[str]):
    for key in keys:
        value = record.get(key)
        if value not in (None, "", "None"):
            return value
    return None


def _to_int(value: Any):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return None


def _call_broker_with_cooldown(callback, *, attempts=3):
    """Retry read-only broker reconciliation calls after a temporary throttle."""
    last_error = None
    for attempt in range(attempts):
        try:
            return callback()
        except Exception as exc:
            last_error = exc
            message = str(exc or "").strip().lower()
            transient = any(marker in message for marker in TRANSIENT_BROKER_MARKERS)
            if not transient or attempt + 1 >= attempts:
                raise
            time.sleep(1.25 * (attempt + 1))
    raise last_error


def _history_contract_symbols(trade_history: Tradeorderhistory) -> set[str]:
    params = trade_history.order_params if isinstance(trade_history.order_params, dict) else {}
    metadata = trade_history.sltp_metadata if isinstance(trade_history.sltp_metadata, dict) else {}
    values = {
        trade_history.trading_symbol,
        params.get("resolved_trading_symbol"),
        params.get("trading_symbol"),
        params.get("tradingsymbol"),
        params.get("trade_symbol"),
        metadata.get("trading_symbol"),
        metadata.get("resolved_trading_symbol"),
    }
    underlying = str(
        params.get("underlying")
        or params.get("symbol")
        or trade_history.Index_Symbol
        or ""
    ).strip().upper()
    strike = params.get("strike_price") or params.get("strike")
    option_type = str(params.get("option_type") or params.get("Type") or "").strip().upper()
    expiry = params.get("expiry")
    try:
        expiry_date = timezone.datetime.fromisoformat(str(expiry)).date() if expiry else None
    except (TypeError, ValueError):
        expiry_date = None
    if underlying and strike not in (None, "") and option_type in {"CE", "PE"} and expiry_date:
        try:
            strike_value = Decimal(str(strike))
            strike_text = (
                str(int(strike_value))
                if strike_value == strike_value.to_integral_value()
                else format(strike_value.normalize(), "f")
            )
            expiry_text = expiry_date.strftime("%d%b%y").upper()
            # Brokers expose the same contract in different orders:
            # Angel/Dhan: NIFTY28JUL2623950PE
            # Upstox:    NIFTY 23950 PE 28 JUL 26
            values.add(f"{underlying}{expiry_text}{strike_text}{option_type}")
            values.add(f"{underlying}{strike_text}{option_type}{expiry_text}")
            # Upstox weekly options use YY + non-zero-padded month + DD:
            # NIFTY2680424100CE => NIFTY, 2026, August, 04, 24100 CE.
            values.add(
                f"{underlying}{expiry_date.strftime('%y')}"
                f"{expiry_date.month}{expiry_date.strftime('%d')}"
                f"{strike_text}{option_type}"
            )
            # Upstox: NIFTY26JUL23950PE
            values.add(f"{underlying}{expiry_date.strftime('%y%b').upper()}{strike_text}{option_type}")
            # Dhan: NIFTY-Jul2026-23800-CE
            values.add(f"{underlying}{expiry_date.strftime('%b%Y').upper()}{strike_text}{option_type}")
        except (ArithmeticError, TypeError, ValueError):
            pass
    return {symbol for value in values if (symbol := _compact_symbol(value))}


def _history_product(trade_history: Tradeorderhistory) -> str:
    params = trade_history.order_params if isinstance(trade_history.order_params, dict) else {}
    return str(params.get("product_type") or params.get("product") or "").strip().upper()


def _record_matches_contract(record: dict[str, Any], symbols: set[str], product: str) -> bool:
    record_symbol = _compact_symbol(_first(record, SYMBOL_KEYS))
    if not record_symbol or record_symbol not in symbols:
        return False
    record_product = str(_first(record, PRODUCT_KEYS) or "").strip().upper()
    expected_product = PRODUCT_ALIASES.get(product, product)
    actual_product = PRODUCT_ALIASES.get(record_product, record_product)
    return not expected_product or not actual_product or actual_product == expected_product


def _known_broker_order_ids(client_id: int) -> set[str]:
    """Return exit order IDs which have already closed a trade successfully.

    Failed/pending SELL histories must remain eligible for broker
    reconciliation: a broker can acknowledge or fill an order after our first
    status lookup timed out. Treating those IDs as consumed prevents a
    subsequently confirmed fill from closing the original BUY row.
    """
    known = set()
    for history in Tradeorderhistory.objects.filter(client_id=client_id).only(
        "transaction_type",
        "trade_order_status",
        "order_status",
        "Exit_status",
        "Exit_Price",
        "order_id",
        "order_params",
        "response_data",
        "webhook_signal",
    ).iterator():
        transaction_type = str(history.transaction_type or "").strip().upper()
        trade_status = str(history.trade_order_status or "").strip().lower()
        order_status = str(history.order_status or "").strip().lower()
        exit_status = str(history.Exit_status or "").strip().lower()
        successful_sell = (
            transaction_type == "SELL"
            and (order_status in SUCCESS_STATUSES or exit_status in SUCCESS_STATUSES)
            and history.Exit_Price is not None
        )
        consolidated_closed_entry = (
            transaction_type == "BUY"
            and trade_status in {"close", "closed"}
            and history.Exit_Price is not None
        )
        if not successful_sell and not consolidated_closed_entry:
            continue
        if history.order_id not in (None, "", "0"):
            known.add(str(history.order_id).strip())
        for payload in (history.order_params, history.response_data, history.webhook_signal):
            for record in _walk_dicts(payload):
                known.update(_record_order_ids(record))
    return known


def _broker_details_for_trade(trade_history: Tradeorderhistory):
    target = normalize_broker_name(trade_history.broker)
    return next(
        (
            details
            for details in ClientBrokerdetails.objects.select_related(
                "broker_name",
                "execution_node",
            ).filter(client_id=trade_history.client_id)
            if normalize_broker_name(getattr(details.broker_name, "broker_name", "")) == target
        ),
        None,
    )


def _position_is_flat(position_response: Any, symbols: set[str], product: str) -> bool:
    matches = [
        record
        for record in _walk_dicts(position_response)
        if _record_matches_contract(record, symbols, product)
        and _first(record, NET_QUANTITY_KEYS) not in (None, "", "None")
    ]
    if not matches:
        return False
    return all(_to_int(_first(record, NET_QUANTITY_KEYS)) == 0 for record in matches)


def _find_unrecorded_external_sell(
    orderbook_response: Any,
    *,
    symbols: set[str],
    product: str,
    entry_time,
    required_quantity: int,
    known_order_ids: set[str],
):
    candidates = []
    for record in _walk_dicts(orderbook_response):
        if not _record_matches_contract(record, symbols, product):
            continue
        transaction_type = str(_first(record, TRANSACTION_KEYS) or "").strip().lower()
        if transaction_type not in SELL_VALUES:
            continue
        status = _record_status(record)
        price = _record_price(record)
        quantity = _record_quantity(record)
        executed_at = _record_execution_time(record)
        order_ids = _record_order_ids(record)
        if (
            status not in SUCCESS_STATUSES
            or price is None
            or quantity is None
            or quantity < required_quantity
            or not executed_at
            or (entry_time and executed_at < entry_time)
            or (order_ids and order_ids.issubset(known_order_ids))
        ):
            continue
        candidates.append((executed_at, record, price, quantity, order_ids))
    return min(candidates, key=lambda item: item[0]) if candidates else None


def reconcile_externally_closed_trade(trade_history: Tradeorderhistory):
    """Close a SaaS BUY row only when broker position and fill both prove closure."""
    if not trade_history or not trade_history.pk or str(trade_history.transaction_type or "").upper() != "BUY":
        return None
    if str(trade_history.trade_order_status or "").upper() in {"CLOSE", "CLOSED"}:
        return None

    symbols = _history_contract_symbols(trade_history)
    required_quantity = int(trade_history.EntryQty or 0)
    if not symbols or required_quantity <= 0:
        return None

    broker_details = _broker_details_for_trade(trade_history)
    if not broker_details or not broker_details.execution_node:
        return None
    proxy_config = build_requests_proxy_config(broker_details.execution_node)
    if not proxy_config:
        return None

    adapter = get_broker_adapter(broker_details)
    positions = _call_broker_with_cooldown(
        lambda: adapter.get_positions(proxy_config=proxy_config)
    )
    product = _history_product(trade_history)
    if not _position_is_flat(positions, symbols, product):
        return None

    orderbook = _call_broker_with_cooldown(
        lambda: adapter.get_orderbook(proxy_config=proxy_config)
    )
    match = _find_unrecorded_external_sell(
        orderbook,
        symbols=symbols,
        product=product,
        entry_time=trade_history.SignalEntry_time,
        required_quantity=required_quantity,
        known_order_ids=_known_broker_order_ids(trade_history.client_id),
    )
    if not match:
        return None

    executed_at, broker_record, exit_price, exit_quantity, order_ids = match
    exit_quantity = min(required_quantity, exit_quantity)
    entry_price = Decimal(str(trade_history.Entry_Price or 0))
    if str(trade_history.Entry_type or "").strip().upper() in {"SELL", "SHORT"}:
        total = (entry_price - exit_price) * exit_quantity
    else:
        total = (exit_price - entry_price) * exit_quantity

    with transaction.atomic():
        locked = Tradeorderhistory.objects.select_for_update().get(pk=trade_history.pk)
        if str(locked.trade_order_status or "").upper() in {"CLOSE", "CLOSED"}:
            return None
        params = dict(locked.order_params or {})
        params["broker_position_reconciliation"] = {
            "source": "broker_orderbook_and_positions",
            "exit_order_ids": sorted(order_ids),
            "broker_status": _record_status(broker_record),
            "filled_quantity": exit_quantity,
            "average_traded_price": float(exit_price),
            "exchange_time": executed_at.isoformat(),
            "verified_net_quantity": 0,
            "reconciled_at": timezone.now().isoformat(),
            "broker_record": json.loads(json.dumps(broker_record, cls=DjangoJSONEncoder)),
        }
        locked.trade_order_status = "CLOSE"
        locked.Exit_type = "BROKER_RECONCILIATION"
        locked.Exit_status = _record_status(broker_record)
        locked.Exit_Price = exit_price
        locked.ExitQty = exit_quantity
        locked.SignalExit_time = executed_at
        locked.Total = total
        locked.order_params = params
        locked.sltp_status = "CLOSED"
        locked.sltp_last_action = "BROKER_RECONCILED"
        locked.sltp_last_failure_reason = None
        locked.sltp_manual_attention = False
        locked.sltp_last_checked_at = timezone.now()
        locked.save(update_fields=[
            "trade_order_status",
            "Exit_type",
            "Exit_status",
            "Exit_Price",
            "ExitQty",
            "SignalExit_time",
            "Total",
            "order_params",
            "sltp_status",
            "sltp_last_action",
            "sltp_last_failure_reason",
            "sltp_manual_attention",
            "sltp_last_checked_at",
        ])
    return {
        "data": {
            "status": "reconciled_closed",
            "message": "The broker position was already closed. The trade was reconciled and moved to Closed.",
            "order_id": next(iter(order_ids), None),
            "executed_price": float(exit_price),
            "filled_quantity": exit_quantity,
            "exchange_time": executed_at.isoformat(),
        }
    }


def reconcile_failed_exit_response(trade_history: Tradeorderhistory, response: Any):
    """Reconcile an external close after a panel exit receives broker failure."""
    response_data = response.get("data", {}) if isinstance(response, dict) else {}
    response_status = str(
        response_data.get("status")
        or (response.get("status") if isinstance(response, dict) else "")
        or ""
    ).strip().lower()
    if response_status in SUCCESS_STATUSES | {"open", "placed", "reconciled_closed"}:
        return response
    try:
        return reconcile_externally_closed_trade(trade_history) or response
    except Exception:
        logger.exception(
            "External broker-position reconciliation failed for trade history %s.",
            getattr(trade_history, "id", None),
        )
        return response
