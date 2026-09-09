"""Record direct webhook exit outcomes; never place, cancel, or replay orders."""
from datetime import timedelta

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from main.models import BrokerOrderIntent, Tradeorderhistory

# These responses prove that our execution engine did not submit, or that the
# broker explicitly rejected the order. Network failures are never retryable
# solely because the response says Failed.
DEFINITIVE_FAILURE_CODES = {
    "DAILY_BROKER_TOKEN_REQUIRED", "MISSING_BROKER", "MISSING_ACCESS_TOKEN",
    "ACCESS_TOKEN_EXPIRED", "MISSING_CREDENTIALS", "INVALID_SESSION",
    "NO_OPEN_BUY_POSITION", "BROKER_ORDER_REJECTED",
}
SUCCESS_STATUSES = {"success", "complete", "completed", "filled", "traded", "executed", "open", "placed", "pending", "accepted"}


def record_direct_webhook_exit_result(intent_id, *, client_id, side, response, history_id=None):
    if not intent_id or str(side).upper() != "SELL":
        return False
    response = response if isinstance(response, dict) else {}
    data = response.get("data") if isinstance(response.get("data"), dict) else response
    status = str(data.get("status") or "").lower()
    code = str(data.get("error_code") or "")
    message = str(data.get("message") or data.get("error") or "Broker submission outcome is unknown.")
    order_id = str(data.get("order_id") or data.get("orderid") or "")
    with transaction.atomic():
        intent = BrokerOrderIntent.objects.select_for_update().filter(
            pk=intent_id, client_id=client_id, kind=BrokerOrderIntent.KIND_EXIT,
            source_type="webhook_exit_direct",
        ).first()
        if not intent or intent.lifecycle_state in {
            BrokerOrderIntent.LIFECYCLE_RECONCILED, BrokerOrderIntent.LIFECYCLE_FILLED,
            BrokerOrderIntent.LIFECYCLE_BROKER_ACCEPTED, BrokerOrderIntent.LIFECYCLE_PARTIAL,
            BrokerOrderIntent.LIFECYCLE_CANCELLED,
        }:
            return False
        closed = Tradeorderhistory.objects.filter(
            pk=intent.exit_trade_history_id,
        ).filter(Q(trade_order_status__iexact="CLOSE") | Q(trade_order_status__iexact="CLOSED")).exists()
        now = timezone.now()
        if closed:
            intent.status = BrokerOrderIntent.STATUS_ACKNOWLEDGED
            intent.lifecycle_state = BrokerOrderIntent.LIFECYCLE_RECONCILED
            intent.remaining_quantity = 0
            intent.reconciled_at = now
            intent.last_error = ""
        elif status in SUCCESS_STATUSES and order_id not in {"", "0"}:
            intent.status = BrokerOrderIntent.STATUS_ACKNOWLEDGED
            intent.lifecycle_state = BrokerOrderIntent.LIFECYCLE_BROKER_ACCEPTED
            intent.broker_order_id = order_id
            intent.broker_accepted_at = now
            intent.last_error = ""
        elif status not in SUCCESS_STATUSES and code in DEFINITIVE_FAILURE_CODES:
            intent.status = BrokerOrderIntent.STATUS_REJECTED
            intent.lifecycle_state = BrokerOrderIntent.LIFECYCLE_ATTENTION
            intent.last_error = message
        else:
            intent.status = BrokerOrderIntent.STATUS_AMBIGUOUS
            intent.lifecycle_state = BrokerOrderIntent.LIFECYCLE_UNCERTAIN
            intent.last_error = message
        intent.outcome = {"status": status, "error_code": code, "message": message, "order_id": order_id, "history_id": str(history_id or "")}
        intent.heartbeat_at = now
        intent.reconcile_after = now
        intent.save(update_fields=["status", "lifecycle_state", "remaining_quantity", "reconciled_at", "broker_order_id", "broker_accepted_at", "last_error", "outcome", "heartbeat_at", "reconcile_after", "updated_at"])
    return True


def mark_stale_direct_webhook_exits(*, now=None):
    """An expired worker heartbeat means uncertainty, never permission to replay."""
    now = now or timezone.now()
    cutoff = now - timedelta(minutes=6)
    return BrokerOrderIntent.objects.filter(
        kind=BrokerOrderIntent.KIND_EXIT, source_type="webhook_exit_direct",
        lifecycle_state=BrokerOrderIntent.LIFECYCLE_SUBMITTING,
    ).filter(Q(heartbeat_at__lt=cutoff) | Q(heartbeat_at__isnull=True, created_at__lt=cutoff)).update(
        status=BrokerOrderIntent.STATUS_AMBIGUOUS,
        lifecycle_state=BrokerOrderIntent.LIFECYCLE_UNCERTAIN,
        last_error="Exit worker finished without a recorded outcome. Broker confirmation is required before another exit; no order was replayed.",
        reconcile_after=now, updated_at=now,
    )


def recover_saved_token_rejection(intent_id, *, now=None):
    """Release a stale direct exit only from its exact persisted token rejection.

    This repairs the ledger; it neither queues an exit nor changes credentials.
    Unknown outcomes and any evidence of broker acceptance remain protected.
    """
    now = now or timezone.now()
    with transaction.atomic():
        intent = BrokerOrderIntent.objects.select_for_update().filter(
            pk=intent_id, kind=BrokerOrderIntent.KIND_EXIT,
            source_type="webhook_exit_direct",
            lifecycle_state=BrokerOrderIntent.LIFECYCLE_UNCERTAIN,
        ).first()
        if not intent or intent.broker_order_id or intent.broker_accepted_at:
            return False
        if (intent.heartbeat_at or intent.created_at) > now - timedelta(minutes=6):
            return False
        trade = Tradeorderhistory.objects.filter(
            pk=intent.exit_trade_history_id, client_id=intent.client_id,
            transaction_type__iexact="BUY",
        ).first()
        if not trade:
            return False
        # Inspect the latest linked result, including successes, rather than
        # selecting an older failure that could hide a later submission.
        history = Tradeorderhistory.objects.filter(
            client_id=intent.client_id, transaction_type__iexact="SELL",
        ).filter(
            Q(order_params__broker_order_intent_id=intent.pk)
            | Q(order_params__broker_order_intent_id=str(intent.pk))
        ).order_by("-pk").first()
        if not history or history.order_id not in (None, "", "0"):
            return False
        params = history.order_params or {}
        identities = {str(trade.pk)}
        if trade.history_id:
            identities.add(str(trade.history_id))
        if str(params.get("original_history_id") or "") not in identities:
            return False
        bound = params.get("webhook_bound_open_history_id")
        if bound is not None and str(bound) not in identities:
            return False
        response = history.response_data if isinstance(history.response_data, dict) else {}
        data = response.get("data") if isinstance(response.get("data"), dict) else response
        if (
            str(data.get("status") or "").lower() not in {"failed", "error", "rejected"}
            or data.get("error_code") != "DAILY_BROKER_TOKEN_REQUIRED"
            or data.get("order_id") not in (None, "", "0", 0)
            or data.get("orderid") not in (None, "", "0", 0)
        ):
            return False
        return record_direct_webhook_exit_result(
            intent.pk, client_id=intent.client_id, side="SELL",
            response=response, history_id=history.history_id or history.pk,
        )
