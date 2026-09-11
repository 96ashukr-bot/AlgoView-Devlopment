"""Cancel an exact unfilled BUY when the user presses Kill Switch.

An accepted limit order is not a position. Never synthesize a SELL, fill,
closing price, or P&L for a zero-fill cancellation.
"""
from decimal import Decimal, InvalidOperation
import time

import requests
from django.db import transaction
from django.utils import timezone
from kiteconnect import KiteConnect

from main.brokers.utils import get_access_token
from main.models import Tradeorderhistory
from main.services.daily_broker_sessions import session_policy_error
from main.services.external_position_reconciliation import _broker_details_for_trade
from main.services.proxy_utils import build_requests_proxy_config

PENDING = {"open", "pending", "trigger pending", "validation pending", "put order req received", "modify pending", "cancel pending"}
TERMINAL = {"cancelled", "canceled", "rejected"}
FILLED = {"complete", "completed", "traded", "filled", "executed"}


def _filled(record):
    # Missing/invalid quantities are uncertain, not zero.
    try:
        value = Decimal(str(record["filled_quantity"]))
        if not value.is_finite() or value < 0 or value != value.to_integral_value():
            raise ValueError
        return int(value)
    except (KeyError, TypeError, ValueError, InvalidOperation):
        raise ValueError("Broker fill quantity is unavailable; cancellation was not confirmed.") from None


def _read_entry(adapter, proxy, trade):
    response = adapter.get_orderbook(proxy_config=proxy)
    if isinstance(response, dict):
        if str(response.get("status") or "").lower() not in {"success", "ok"}:
            raise ValueError("Broker order book is unavailable. Retry Kill Switch after checking the broker session.")
        response = response.get("data")
    if not isinstance(response, list):
        raise ValueError("Broker order book is unavailable; no order was cancelled.")
    rows = [r for r in response if isinstance(r, dict) and str(r.get("order_id")) == str(trade.order_id)]
    if len(rows) != 1 or str(rows[0].get("transaction_type") or "").upper() != "BUY":
        raise ValueError("The exact BUY order could not be verified; no order was cancelled.")
    _filled(rows[0])
    return rows[0]


def _cancel_entry(details, proxy, record, broker):
    order_id = str(record["order_id"])
    if broker == "zerodha":
        variety = str(record.get("variety") or "regular").lower()
        if variety != "regular":
            raise ValueError("Cancel this special-variety pending order directly in the broker app.")
        kite = KiteConnect(api_key=details.broker_API_KEY, proxies=proxy, timeout=10)
        kite.set_access_token(get_access_token(details))
        kite.cancel_order(variety=variety, order_id=order_id)
    else:
        response = requests.delete(
            "https://api-hft.upstox.com/v3/order/cancel",
            params={"order_id": order_id},
            headers={"Accept": "application/json", "Authorization": f"Bearer {get_access_token(details)}"},
            proxies=proxy, timeout=10,
        )
        response.raise_for_status()
        if response.json().get("status") != "success":
            raise ValueError("Upstox did not acknowledge cancellation.")


def _record_terminal_unfilled(trade, record, initiated_by_id):
    broker_status = str(record.get("status") or "").lower()
    if broker_status not in TERMINAL or _filled(record) != 0:
        raise ValueError("Cannot mark an executed or unconfirmed BUY as cancelled.")
    message = f"Pending BUY {broker_status} at broker; no quantity executed and no SELL was submitted."
    with transaction.atomic():
        locked = Tradeorderhistory.objects.select_for_update().get(pk=trade.pk, client_id=trade.client_id)
        if str(locked.order_id) != str(record["order_id"]) or str(locked.transaction_type).upper() != "BUY":
            raise ValueError("Trade identity changed during cancellation. Refresh the panel.")
        if str(locked.trade_order_status).lower() in {"close", "closed"}:
            raise ValueError("Trade was reconciled concurrently. Refresh the panel.")
        params = dict(locked.order_params or {})
        params["pending_entry_cancellation"] = {
            "broker_order_id": str(record["order_id"]), "broker_status": broker_status,
            "filled_quantity": 0, "requested_quantity": record.get("quantity"),
            "limit_price": record.get("price"), "verified_at": timezone.now().isoformat(),
            "initiated_by_id": initiated_by_id,
        }
        locked.order_params = params
        locked.order_status = broker_status
        locked.Entry_status = broker_status
        locked.trade_order_status = "CANCELLED" if broker_status in {"cancelled", "canceled"} else "Failed"
        locked.Entry_Price = None
        locked.Exit_Price = None
        locked.ExitQty = None
        locked.Exit_status = None
        locked.Exit_type = None
        locked.SignalExit_time = None
        locked.Total = None
        locked.failure_reason = message
        locked.sltp_status = "ENTRY_CANCELLED"
        locked.sltp_last_action = "KILL_SWITCH_CANCELLED_ENTRY"
        locked.sltp_last_failure_reason = None
        locked.sltp_manual_attention = False
        locked.save(update_fields=["order_params", "order_status", "Entry_status", "trade_order_status",
            "Entry_Price", "Exit_Price", "ExitQty", "Exit_status", "Exit_type", "SignalExit_time", "Total",
            "failure_reason", "sltp_status", "sltp_last_action", "sltp_last_failure_reason", "sltp_manual_attention"])
    trade.refresh_from_db()
    return {"status": "cancelled_entry", "trade_history_id": trade.id, "client_id": trade.client_id,
            "message": message, "order_id": str(record["order_id"]), "filled_quantity": 0}


def handle_pending_entry_kill_switch(trade, *, initiated_by_id=None):
    """Return a cancellation result, or None for the existing filled-exit path.

    Called only from authenticated, client-authorized Kill Switch views.
    Partial fills remain blocked for explicit review rather than being treated
    as a cancelled position or risking an oversell.
    """
    broker = str(trade.broker or "").strip().lower()
    if broker not in {"zerodha", "upstox"} or str(trade.transaction_type).upper() != "BUY":
        return None
    if str(trade.order_status or "").strip().lower() not in PENDING:
        return None
    details = _broker_details_for_trade(trade)
    error = session_policy_error(details, refresh=True) if details else "Broker session is missing."
    if error:
        raise ValueError(error)
    proxy = build_requests_proxy_config(details.execution_node) if details.execution_node else None
    if not proxy:
        raise ValueError("Assigned broker proxy is missing; no order was cancelled.")
    from main.brokers.registry import get_broker_adapter
    from main.tasks import acquire_force_kill_dispatch, release_force_kill_dispatch
    dispatch = acquire_force_kill_dispatch(trade.id)
    if not dispatch:
        raise ValueError("Kill Switch is already processing this order. Refresh shortly.")
    try:
        adapter = get_broker_adapter(details)
        record = _read_entry(adapter, proxy, trade)
        status = str(record.get("status") or "").lower()
        if status in FILLED and _filled(record) > 0:
            # reserve_exit_intent will recover the confirmed BUY snapshot.
            return None
        if _filled(record) > 0:
            raise ValueError("BUY is partially filled. Review/cancel its pending remainder in the broker app before exiting the filled position.")
        if status in TERMINAL:
            return _record_terminal_unfilled(trade, record, initiated_by_id)
        if status not in PENDING:
            raise ValueError("Broker entry status is uncertain; no SELL was submitted.")
        try:
            _cancel_entry(details, proxy, record, broker)
        except Exception:
            # A timeout may occur after acceptance. Read back the exact order;
            # never assume cancellation or resend blindly.
            pass
        for attempt in range(3):
            record = _read_entry(adapter, proxy, trade)
            status = str(record.get("status") or "").lower()
            if _filled(record) > 0:
                raise ValueError("BUY filled while cancellation was being checked. No SELL was submitted; refresh broker positions before retrying Kill Switch.")
            if status in TERMINAL:
                return _record_terminal_unfilled(trade, record, initiated_by_id)
            if attempt < 2:
                time.sleep(0.3)
        raise ValueError("Pending BUY cancellation is not confirmed. Check its broker status before retrying Kill Switch.")
    finally:
        release_force_kill_dispatch(trade.id, dispatch)
