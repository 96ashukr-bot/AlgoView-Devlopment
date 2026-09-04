"""Unified durable lifecycle for Kill Switch, SL/TP, and webhook exits."""
from __future__ import annotations

from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from django.db import transaction
from django.db.models import Max, Q
from django.utils import timezone

from main.brokers.contract_snapshot import (
    build_broker_contract_snapshot,
    immutable_snapshot,
    recoverable_exit_snapshot,
    valid_snapshot,
)
from main.models import BrokerOrderFill, BrokerOrderIntent, Tradeorderhistory
from main.services.order_streams import create_intent


ACTIVE_LIFECYCLES = {
    BrokerOrderIntent.LIFECYCLE_TRIGGERED,
    BrokerOrderIntent.LIFECYCLE_QUEUED,
    BrokerOrderIntent.LIFECYCLE_SUBMITTING,
    BrokerOrderIntent.LIFECYCLE_BROKER_ACCEPTED,
    BrokerOrderIntent.LIFECYCLE_PARTIAL,
    BrokerOrderIntent.LIFECYCLE_UNCERTAIN,
}


def _source_event(source: str, *, trigger_id: str = "", metadata: dict | None = None) -> dict:
    return {
        "source": str(source or "unknown").strip().lower(),
        "trigger_id": str(trigger_id or ""),
        "triggered_at": timezone.now().isoformat(),
        "metadata": deepcopy(metadata or {}),
    }


def _snapshot_for_buy(trade: Tradeorderhistory) -> dict:
    params = trade.order_params if isinstance(trade.order_params, dict) else {}
    response = trade.response_data if isinstance(trade.response_data, dict) else {}
    sltp = trade.sltp_metadata if isinstance(trade.sltp_metadata, dict) else {}
    snapshot = immutable_snapshot(params, response, sltp)
    if snapshot:
        return snapshot
    expected_order_id = trade.order_id
    for source in (params, response, sltp):
        candidate = source.get("broker_contract_snapshot") if isinstance(source, dict) else None
        recovered = recoverable_exit_snapshot(candidate, expected_buy_order_id=expected_order_id)
        if recovered:
            return recovered
    # Legacy/manual Demo Broker BUY rows predate the canonical simulated
    # contract snapshot and may contain only the underlying (for example
    # ``NIFTY``) with a null exchange.  Demo has no remote demat position, so
    # reconstructing its exact simulated identity from the immutable BUY row
    # is safe and prevents Kill Switch/SLTP from becoming permanently blocked.
    # Live brokers deliberately remain fail-closed above.
    if str(trade.broker or "").strip().lower() in {"demo", "demo broker"}:
        underlying = str(
            params.get("underlying") or params.get("symbol")
            or sltp.get("underlying") or trade.Index_Symbol or ""
        ).strip().upper()
        expiry = str(params.get("expiry") or sltp.get("expiry") or "").split("T", 1)[0]
        strike = params.get("strike") if params.get("strike") not in (None, "") else params.get("strike_price")
        option_type = str(params.get("option_type") or params.get("Type") or sltp.get("option_type") or "").strip().upper()
        try:
            expiry_date = datetime.strptime(expiry, "%Y-%m-%d").date()
            strike_number = float(strike)
            strike_text = str(int(strike_number)) if strike_number.is_integer() else str(strike_number).rstrip("0").rstrip(".")
            contract_symbol = f"{underlying}{expiry_date.strftime('%d%b%y').upper()}{strike_text}{option_type}"
        except (TypeError, ValueError):
            contract_symbol = ""
        if contract_symbol and option_type in {"CE", "PE"}:
            rebuilt = build_broker_contract_snapshot(
                broker_name="Demo Broker",
                fields={
                    "original_broker_trading_symbol": contract_symbol,
                    "original_broker_instrument_key": contract_symbol,
                    "original_broker_exchange": trade.Exchange or params.get("Exchange") or "NFO",
                    "original_broker_product_type": params.get("original_broker_product_type") or params.get("product_type") or "MIS",
                    "original_broker_quantity": trade.EntryQty,
                },
                underlying=underlying,
                expiry=expiry,
                strike=strike,
                option_type=option_type,
                buy_order_id=trade.order_id,
                filled_quantity=trade.EntryQty,
            )
            if valid_snapshot(rebuilt):
                return rebuilt
    raise ValueError(
        "The selected BUY does not contain a broker-confirmed contract snapshot. "
        "Exit was blocked to prevent selling an incorrect contract."
    )


def _remaining_quantity(trade: Tradeorderhistory, snapshot: dict) -> int:
    entry = trade.EntryQty or snapshot.get("filled_quantity") or 0
    try:
        entry = max(int(float(entry or 0)), 0)
    except (TypeError, ValueError):
        entry = 0
    # ExitQty is provisional on some legacy Kill Switch rows. Only consume it
    # when the BUY lifecycle is broker-confirmed closed.
    closed = str(trade.trade_order_status or "").strip().upper() in {"CLOSE", "CLOSED"}
    exited = trade.ExitQty if closed else 0
    try:
        exited = max(int(float(exited or 0)), 0)
    except (TypeError, ValueError):
        exited = 0
    return max(entry - exited, 0)


def reserve_exit_intent(
    *, trade: Tradeorderhistory, source: str, source_type: str,
    trigger_id: str = "", payload: dict | None = None,
    publish: bool = True,
) -> tuple[BrokerOrderIntent, bool]:
    """Create or join the one active exit generation for an exact BUY.

    The BUY row lock and unique generation constraint are the authoritative
    duplicate protection. Redis publication happens after commit via the
    existing durable outbox.
    """
    with transaction.atomic():
        locked = Tradeorderhistory.objects.select_for_update().select_related("client").get(pk=trade.pk)
        existing = BrokerOrderIntent.objects.select_for_update().filter(
            kind=BrokerOrderIntent.KIND_EXIT,
            exit_trade_history=locked,
            lifecycle_state__in=ACTIVE_LIFECYCLES,
        ).order_by("-exit_generation", "-id").first()
        event = _source_event(source, trigger_id=trigger_id, metadata=payload)
        if existing:
            sources = list(existing.trigger_sources or [])
            if not any(item.get("source") == event["source"] and item.get("trigger_id") == event["trigger_id"]
                       for item in sources if isinstance(item, dict)):
                sources.append(event)
                existing.trigger_sources = sources
                existing.save(update_fields=["trigger_sources", "updated_at"])
            return existing, False

        snapshot = _snapshot_for_buy(locked)
        quantity = _remaining_quantity(locked, snapshot)
        if quantity <= 0:
            raise ValueError("The selected BUY has no remaining quantity to exit.")
        generation = (
            BrokerOrderIntent.objects.filter(
                kind=BrokerOrderIntent.KIND_EXIT, exit_trade_history=locked,
            ).aggregate(value=Max("exit_generation"))["value"] or 0
        ) + 1
        safe_payload = deepcopy(payload or {})
        safe_payload.update({
            "trade_history_id": locked.id,
            "original_history_id": locked.history_id or locked.id,
            "exit_generation": generation,
            "contract_snapshot": snapshot,
            "requested_quantity": quantity,
        })
        intent, created = create_intent(
            idempotency_key=f"exit:{locked.id}:{generation}",
            kind=BrokerOrderIntent.KIND_EXIT,
            broker=locked.broker,
            client_id=locked.client_id,
            source_type=source_type,
            source_id=str(locked.id),
            payload=safe_payload,
            exit_trade_history_id=locked.id,
            exit_generation=generation,
            trigger_sources=[event],
            contract_snapshot=snapshot,
            requested_quantity=quantity,
            publish=publish,
        )
        return intent, created


def bind_webhook_intent_to_buy(intent_id: int | None, trade: Tradeorderhistory, *, trigger_id: str = ""):
    """Bind a generic webhook Stream intent before its broker call begins."""
    if not intent_id:
        return None
    with transaction.atomic():
        locked_trade = Tradeorderhistory.objects.select_for_update().get(pk=trade.pk)
        intent = BrokerOrderIntent.objects.select_for_update().filter(
            pk=intent_id, kind=BrokerOrderIntent.KIND_EXIT,
        ).first()
        if intent is None:
            return None
        if intent.exit_trade_history_id and intent.exit_trade_history_id != locked_trade.id:
            raise ValueError("Webhook exit intent is already bound to a different BUY.")
        existing = BrokerOrderIntent.objects.select_for_update().filter(
            kind=BrokerOrderIntent.KIND_EXIT,
            exit_trade_history=locked_trade,
            lifecycle_state__in=ACTIVE_LIFECYCLES,
        ).exclude(pk=intent.pk).order_by("-exit_generation", "-id").first()
        if existing:
            event = _source_event("webhook", trigger_id=trigger_id)
            existing.trigger_sources = list(existing.trigger_sources or []) + [event]
            existing.save(update_fields=["trigger_sources", "updated_at"])
            intent.status = BrokerOrderIntent.STATUS_CANCELLED
            intent.lifecycle_state = BrokerOrderIntent.LIFECYCLE_CANCELLED
            intent.last_error = f"Joined active exit intent {existing.id} for the same BUY."
            intent.save(update_fields=["status", "lifecycle_state", "last_error", "updated_at"])
            return existing
        snapshot = _snapshot_for_buy(locked_trade)
        quantity = _remaining_quantity(locked_trade, snapshot)
        if quantity <= 0:
            raise ValueError("The webhook-selected BUY has no remaining quantity to exit.")
        generation = intent.exit_generation
        if not generation:
            generation = (
                BrokerOrderIntent.objects.filter(
                    kind=BrokerOrderIntent.KIND_EXIT, exit_trade_history=locked_trade,
                ).exclude(pk=intent.pk).aggregate(value=Max("exit_generation"))["value"] or 0
            ) + 1
        event = _source_event("webhook", trigger_id=trigger_id)
        intent.exit_trade_history = locked_trade
        intent.exit_generation = generation
        intent.contract_snapshot = snapshot
        intent.requested_quantity = quantity
        intent.remaining_quantity = quantity
        intent.trigger_sources = list(intent.trigger_sources or []) + [event]
        payload = dict(intent.payload or {})
        payload.update({
            "trade_history_id": locked_trade.id,
            "original_history_id": locked_trade.history_id or locked_trade.id,
            "exit_generation": generation,
            "contract_snapshot": snapshot,
            "requested_quantity": quantity,
        })
        intent.payload = payload
        intent.save(update_fields=[
            "exit_trade_history", "exit_generation", "contract_snapshot",
            "requested_quantity", "remaining_quantity", "trigger_sources", "payload", "updated_at",
        ])
        return intent


def record_fill(*, intent_id: int, quantity: Any, price: Any, broker_order_id: str = "",
                broker_trade_id: str = "", executed_at=None, raw_fill: dict | None = None):
    try:
        quantity = int(float(quantity))
        price = Decimal(str(price))
    except (TypeError, ValueError, InvalidOperation):
        return None
    if quantity <= 0 or price <= 0:
        return None
    with transaction.atomic():
        intent = BrokerOrderIntent.objects.select_for_update().get(pk=intent_id)
        fill, created = BrokerOrderFill.objects.get_or_create(
            intent=intent,
            broker_order_id=str(broker_order_id or intent.broker_order_id or ""),
            broker_trade_id=str(broker_trade_id or f"aggregate:{quantity}:{price}"),
            defaults={"quantity": quantity, "price": price, "executed_at": executed_at, "raw_fill": raw_fill or {}},
        )
        if created:
            total = sum(item.quantity for item in intent.fills.all())
            intent.filled_quantity = min(total, intent.requested_quantity or total)
            intent.remaining_quantity = max((intent.requested_quantity or total) - intent.filled_quantity, 0)
            intent.lifecycle_state = (
                BrokerOrderIntent.LIFECYCLE_FILLED if intent.remaining_quantity == 0
                else BrokerOrderIntent.LIFECYCLE_PARTIAL
            )
            if intent.remaining_quantity == 0:
                intent.filled_at = timezone.now()
            intent.save(update_fields=[
                "filled_quantity", "remaining_quantity", "lifecycle_state", "filled_at", "updated_at",
            ])
        return fill


def reconcile_intent_from_trade(intent_id: int) -> bool:
    with transaction.atomic():
        # exit_trade_history is nullable. PostgreSQL rejects SELECT FOR UPDATE
        # when select_related turns that relation into a nullable OUTER JOIN.
        # Lock only the intent row, then load the referenced BUY separately.
        intent = BrokerOrderIntent.objects.select_for_update().filter(pk=intent_id).first()
        if not intent or not intent.exit_trade_history_id:
            return False
        trade = Tradeorderhistory.objects.filter(pk=intent.exit_trade_history_id).first()
        if trade is None:
            return False
        if str(trade.trade_order_status or "").strip().upper() not in {"CLOSE", "CLOSED"}:
            return False
        intent.lifecycle_state = BrokerOrderIntent.LIFECYCLE_RECONCILED
        intent.remaining_quantity = 0
        intent.reconciled_at = timezone.now()
        intent.save(update_fields=["lifecycle_state", "remaining_quantity", "reconciled_at", "updated_at"])
        return True


def record_trade_exit_fill(
    trade: Tradeorderhistory, *, quantity: Any, price: Any,
    broker_order_id: str = "", broker_trade_id: str = "",
    executed_at=None, raw_fill: dict | None = None,
) -> bool:
    """Attach a broker-confirmed SELL fill to the exact BUY exit lifecycle."""
    buy = trade
    if str(trade.transaction_type or "").strip().upper() == "SELL":
        params = trade.order_params if isinstance(trade.order_params, dict) else {}
        signal = trade.webhook_signal if isinstance(trade.webhook_signal, dict) else {}
        original_id = params.get("original_history_id") or signal.get("original_history_id")
        if original_id:
            identity = Q(history_id=original_id)
            if str(original_id).isdigit():
                identity |= Q(pk=int(original_id))
            buy = Tradeorderhistory.objects.filter(
                client_id=trade.client_id,
            ).filter(
                transaction_type__iexact="BUY",
            ).filter(identity).order_by("-id").first()
    if not buy:
        return False
    intent = BrokerOrderIntent.objects.filter(
        kind=BrokerOrderIntent.KIND_EXIT,
        exit_trade_history=buy,
        lifecycle_state__in=ACTIVE_LIFECYCLES | {
            BrokerOrderIntent.LIFECYCLE_FILLED,
        },
    ).order_by("-exit_generation", "-id").first()
    if not intent:
        return False
    record_fill(
        intent_id=intent.id,
        quantity=quantity,
        price=price,
        broker_order_id=broker_order_id,
        broker_trade_id=broker_trade_id,
        executed_at=executed_at,
        raw_fill=raw_fill,
    )
    reconcile_intent_from_trade(intent.id)
    return True
