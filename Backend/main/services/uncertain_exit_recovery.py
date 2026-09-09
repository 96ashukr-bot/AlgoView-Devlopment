"""Reconcile stale direct exits using repeated broker reads; never submit orders."""
import hashlib
import json
from datetime import timedelta

from django.db import transaction
from django.utils import timezone
from django.utils.dateparse import parse_datetime

from main.broker_registry import normalize_broker_name
from main.brokers.registry import get_broker_adapter
from main.models import BrokerOrderIntent, Tradeorderhistory
from main.services.daily_broker_sessions import IST, session_policy_error
from main.services.external_position_reconciliation import _broker_details_for_trade
from main.services.proxy_utils import build_requests_proxy_config

OBSERVATION_KEY = "no_sell_order_observation"


def _integer(value):
    try:
        number = int(value)
        return number if str(value).strip() == str(number) else None
    except (ValueError, TypeError):
        return None


def _open_without_sell(snapshot, orders, positions, *, broker, required_quantity):
    """Require a complete book, the exact filled BUY, and fully unsold quantity."""
    if broker == "upstox":
        if not isinstance(orders, dict) or orders.get("status") != "success":
            return None
        if not isinstance(positions, dict) or positions.get("status") != "success":
            return None
        orders, positions = orders.get("data"), positions.get("data")
    elif broker == "zerodha":
        positions = positions.get("net") if isinstance(positions, dict) else None
    else:
        return None
    if not isinstance(orders, list) or not isinstance(positions, list):
        return None
    if not all(isinstance(row, dict) for row in orders + positions):
        return None
    instrument = str(snapshot.get("broker_instrument_id") or "")
    symbol = str(snapshot.get("broker_trading_symbol") or "")
    exchange = str(snapshot.get("broker_exchange") or "")
    product = str(snapshot.get("broker_product_type") or "")
    buy_id = str(snapshot.get("buy_order_id") or "")
    if not all((instrument, symbol, exchange, product, buy_id)) or required_quantity <= 0:
        return None

    def related(row):
        return str(row.get("instrument_token") or "") == instrument or str(row.get("tradingsymbol") or row.get("trading_symbol") or "") == symbol

    def exact(row):
        return (str(row.get("instrument_token") or "") == instrument
                and str(row.get("tradingsymbol") or row.get("trading_symbol") or "") == symbol
                and row.get("exchange") == exchange and row.get("product") == product)

    matching = [row for row in orders if related(row)]
    # Even rejected/cancelled SELLs are excluded here: this recovery is for
    # an absent order, not for interpreting another broker order's lifecycle.
    if any(str(row.get("transaction_type") or "").upper() != "BUY" for row in matching):
        return None
    buys = [row for row in matching if exact(row)]
    original = [row for row in buys if str(row.get("order_id")) == buy_id]
    if len(original) != 1 or str(original[0].get("status") or "").lower() != "complete":
        return None
    original_fill = _integer(original[0].get("filled_quantity"))
    if original_fill is None or original_fill < required_quantity:
        return None
    fills = [_integer(row.get("filled_quantity")) for row in buys]
    if any(value is None or value < 0 for value in fills):
        return None
    live = [row for row in positions if exact(row)]
    if len(live) != 1:
        return None
    position = live[0]
    net = _integer(position.get("quantity"))
    bought = _integer(position.get("day_buy_quantity"))
    sold = _integer(position.get("day_sell_quantity"))
    overnight = _integer(position.get("overnight_quantity"))
    if net is None or net < required_quantity or sold != 0 or overnight != 0:
        return None
    if bought != net or sum(fills) != net:
        return None
    return {"buy_order_id": buy_id, "instrument": instrument, "symbol": symbol,
            "exchange": exchange, "product": product, "net_quantity": net,
            "buy_fills": sorted((str(row.get("order_id")), qty) for row, qty in zip(buys, fills)),
            "sell_orders": 0}


def _eligible(intent, now):
    return bool(intent and intent.kind == "exit" and intent.source_type == "webhook_exit_direct"
                and intent.lifecycle_state == BrokerOrderIntent.LIFECYCLE_UNCERTAIN
                and not intent.broker_order_id and not intent.broker_accepted_at
                and not intent.filled_quantity
                and (intent.heartbeat_at or intent.created_at) <= now - timedelta(minutes=6))


def recover_broker_absent_exit(intent_id):
    """Return observing/released only after broker proof; callers never replay."""
    now = timezone.now()
    intent = BrokerOrderIntent.objects.filter(pk=intent_id).first()
    if not _eligible(intent, now):
        return None
    trade = Tradeorderhistory.objects.filter(pk=intent.exit_trade_history_id, client_id=intent.client_id, transaction_type__iexact="BUY").first()
    if not trade or str(trade.trade_order_status or "").upper() in {"CLOSE", "CLOSED"}:
        return None
    if intent.created_at.astimezone(IST).date() != now.astimezone(IST).date():
        return None  # Daily order books cannot prove absence on an earlier day.
    snapshot = (trade.order_params or {}).get("broker_contract_snapshot") or {}
    if str(snapshot.get("buy_order_id") or "") != str(trade.order_id or ""):
        return None
    broker = normalize_broker_name(trade.broker)
    if broker not in {"zerodha", "upstox"}:
        return None
    details = _broker_details_for_trade(trade)
    if not details or not details.execution_node_id or session_policy_error(details):
        return None
    evidence = None
    try:
        proxy = build_requests_proxy_config(details.execution_node)
        if not proxy:
            return None
        adapter = get_broker_adapter(details)
        orders = adapter.get_orderbook(proxy_config=proxy)
        positions = adapter.get_positions(proxy_config=proxy)
        evidence = _open_without_sell(snapshot, orders, positions, broker=broker, required_quantity=intent.requested_quantity)
    except Exception:
        evidence = None
    observed_at = timezone.now()
    with transaction.atomic():
        locked = BrokerOrderIntent.objects.select_for_update().get(pk=intent.pk)
        if not _eligible(locked, observed_at) or locked.heartbeat_at != intent.heartbeat_at:
            return None
        outcome = dict(locked.outcome or {})
        if not evidence:
            if outcome.pop(OBSERVATION_KEY, None) is not None:
                locked.outcome = outcome
                locked.save(update_fields=["outcome", "updated_at"])
            return None
        fingerprint = hashlib.sha256(json.dumps(evidence, sort_keys=True).encode()).hexdigest()
        previous = outcome.get(OBSERVATION_KEY) or {}
        previous_at = parse_datetime(str(previous.get("observed_at") or ""))
        elapsed = (observed_at - previous_at).total_seconds() if previous_at and timezone.is_aware(previous_at) else None
        if previous.get("fingerprint") != fingerprint or elapsed is None or elapsed > 90:
            outcome[OBSERVATION_KEY] = {"fingerprint": fingerprint, "observed_at": observed_at.isoformat(), "evidence": evidence}
            locked.outcome = outcome
            locked.reconcile_after = observed_at + timedelta(seconds=10)
            locked.save(update_fields=["outcome", "reconcile_after", "updated_at"])
            return "observing"
        if elapsed < 10:
            return "observing"
        locked.status = BrokerOrderIntent.STATUS_REJECTED
        locked.lifecycle_state = BrokerOrderIntent.LIFECYCLE_ATTENTION
        locked.last_error = "Two broker checks confirmed this BUY remains open with no SELL order. The old exit attempt was cleared; a fresh exit may be requested."
        outcome["broker_absence_recovery"] = {"first_checked_at": previous_at.isoformat(), "confirmed_at": observed_at.isoformat(), "evidence": evidence, "orders_replayed": False}
        locked.outcome = outcome
        locked.reconcile_after = None
        locked.save(update_fields=["status", "lifecycle_state", "last_error", "outcome", "reconcile_after", "updated_at"])
        return "released"
