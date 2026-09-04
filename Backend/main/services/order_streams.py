"""Durable Redis Stream transport for low-latency broker execution.

PostgreSQL owns intent state. Streams only transport credential-free references.
"""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
import uuid
from datetime import timedelta

from django.conf import settings
from django.db import close_old_connections, connections, transaction
from django.db.models import Case, CharField, Value, When
from django.utils import timezone

from main.broker_registry import normalize_broker_name
from main.models import BrokerOrderIntent

logger = logging.getLogger("main")
_QUEUE_WARNING_LOCK = threading.Lock()
_QUEUE_WARNING_LAST: dict[str, float] = {}

BROKER_SLUGS = {
    "angel one": "angelone", "angelone": "angelone", "zerodha": "zerodha", "upstox": "upstox",
    "groww": "groww", "dhan": "dhan", "alice blue": "aliceblue",
    "aliceblue": "aliceblue", "fyers": "fyers", "demo broker": "demo", "demo": "demo",
    "5paisa": "5paisa", "five paisa": "5paisa", "fivepaisa": "5paisa",
}
SECRET_KEYS = {
    "password", "client_secret", "client_secrete", "api_secret", "access_token",
    "refresh_token", "auth_token", "jwt_token", "feed_token", "api_key", "apikey",
    "totp", "totp_secret", "mpin", "pin", "node_secret",
}
TERMINAL = {
    BrokerOrderIntent.STATUS_ACKNOWLEDGED, BrokerOrderIntent.STATUS_REJECTED,
    BrokerOrderIntent.STATUS_DEAD_LETTER, BrokerOrderIntent.STATUS_CANCELLED,
}


def redis_client():
    import redis
    return redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_timeout=2)


def broker_slug(broker: str) -> str:
    normalized = normalize_broker_name(broker).casefold()
    slug = BROKER_SLUGS.get(normalized)
    if not slug:
        raise ValueError(f"Unsupported stream broker: {broker}")
    return slug


def stream_name(*, broker: str, kind: str) -> str:
    priority = "exit" if kind == BrokerOrderIntent.KIND_EXIT else "entry"
    return f"orders:{priority}:{broker_slug(broker)}"


def _assert_credential_free(value, path="payload"):
    if isinstance(value, dict):
        for key, child in value.items():
            lowered = str(key).casefold().replace("-", "_")
            if lowered in SECRET_KEYS or lowered.endswith("_password") or lowered.endswith("_secret"):
                raise ValueError(f"Credential-like field is forbidden in stream payload: {path}.{key}")
            _assert_credential_free(child, f"{path}.{key}")
    elif isinstance(value, (list, tuple)):
        for index, child in enumerate(value):
            _assert_credential_free(child, f"{path}[{index}]")


def create_intent(*, idempotency_key: str, kind: str, broker: str, client_id: int,
                  source_type: str, source_id: str, payload: dict | None = None,
                  exit_trade_history_id: int | None = None, exit_generation: int = 0,
                  trigger_sources: list | None = None, contract_snapshot: dict | None = None,
                  requested_quantity: int = 0, publish: bool = True) -> tuple[BrokerOrderIntent, bool]:
    """Reserve a durable intent; repeated publication returns the original row."""
    safe_payload = dict(payload or {})
    _assert_credential_free(safe_payload)
    partition = f"{broker_slug(broker)}:{int(client_id)}"
    with transaction.atomic():
        intent, created = BrokerOrderIntent.objects.get_or_create(
            idempotency_key=idempotency_key,
            defaults={
                "kind": kind, "broker": normalize_broker_name(broker), "client_id": client_id,
                "account_partition": partition, "source_type": source_type,
                "source_id": str(source_id), "payload": safe_payload,
                "exit_trade_history_id": exit_trade_history_id,
                "exit_generation": int(exit_generation or 0),
                "lifecycle_state": (
                    BrokerOrderIntent.LIFECYCLE_TRIGGERED
                    if kind == BrokerOrderIntent.KIND_EXIT else BrokerOrderIntent.LIFECYCLE_QUEUED
                ),
                "trigger_sources": list(trigger_sources or []),
                "contract_snapshot": dict(contract_snapshot or {}),
                "requested_quantity": max(int(requested_quantity or 0), 0),
                "remaining_quantity": max(int(requested_quantity or 0), 0),
            },
        )
        if created and publish:
            transaction.on_commit(lambda: _publish_after_commit(intent.pk))
        elif created and kind == BrokerOrderIntent.KIND_EXIT:
            intent.status = BrokerOrderIntent.STATUS_PUBLISHED
            intent.lifecycle_state = BrokerOrderIntent.LIFECYCLE_QUEUED
            intent.published_at = timezone.now()
            intent.save(update_fields=["status", "lifecycle_state", "published_at", "updated_at"])
    return intent, created


def create_intents_batch(specs: list[dict]) -> dict[str, BrokerOrderIntent]:
    """Durably reserve and publish a fan-out without per-client round trips."""
    if not specs:
        return {}
    keys = []
    rows = []
    for spec in specs:
        key = str(spec["idempotency_key"])
        payload = dict(spec.get("payload") or {})
        _assert_credential_free(payload)
        broker = normalize_broker_name(spec["broker"])
        client_id = int(spec["client_id"])
        keys.append(key)
        rows.append(BrokerOrderIntent(
            idempotency_key=key,
            kind=spec["kind"],
            broker=broker,
            client_id=client_id,
            account_partition=f"{broker_slug(broker)}:{client_id}",
            source_type=spec["source_type"],
            source_id=str(spec["source_id"]),
            payload=payload,
        ))
    if len(keys) != len(set(keys)):
        raise ValueError("Duplicate idempotency keys in order intent batch")
    with transaction.atomic():
        BrokerOrderIntent.objects.bulk_create(rows, batch_size=500, ignore_conflicts=True)
        intents = list(BrokerOrderIntent.objects.filter(idempotency_key__in=keys))
        publish_ids = [intent.pk for intent in intents if intent.status == BrokerOrderIntent.STATUS_RESERVED]
        transaction.on_commit(lambda: _publish_batch_after_commit(publish_ids))
    by_key = {intent.idempotency_key: intent for intent in intents}
    if len(by_key) != len(keys):
        raise RuntimeError("Could not reserve every order intent in batch")
    return by_key


def _publish_after_commit(intent_id: int) -> None:
    try:
        publish_intent(intent_id)
    except Exception:
        # The RESERVED database row is the outbox. Redis interruption must not
        # make the HTTP request report a false hard failure or lose the order.
        logger.exception("Order intent retained in outbox after Stream publication failure intent_id=%s", intent_id)


def _publish_batch_after_commit(intent_ids: list[int]) -> None:
    try:
        publish_intents_batch(intent_ids)
    except Exception:
        logger.exception(
            "Order intent batch retained in outbox after Stream publication failure count=%s",
            len(intent_ids),
        )


def publish_intent(intent_id: int) -> str | None:
    """Publish once. RESERVED rows are a durable outbox when Redis is unavailable."""
    intent = BrokerOrderIntent.objects.filter(pk=intent_id).first()
    if not intent or intent.status != BrokerOrderIntent.STATUS_RESERVED:
        return getattr(intent, "stream_message_id", None)
    target = stream_name(broker=intent.broker, kind=intent.kind)
    client = redis_client()
    lock_key = f"orders:publish:lock:{intent.pk}"
    owner = uuid.uuid4().hex
    if not client.set(lock_key, owner, nx=True, ex=30):
        return None
    updated = False
    try:
        # Another publisher may have completed between our initial row read and
        # lease acquisition. Re-read under the lease before emitting XADD.
        current = BrokerOrderIntent.objects.filter(pk=intent.pk).values(
            "status", "stream_message_id",
        ).first()
        if not current or current["status"] != BrokerOrderIntent.STATUS_RESERVED:
            updated = True  # Safe to release a lease that emitted no message.
            return current.get("stream_message_id") if current else None
        message_id = client.xadd(target, {
            "intent_id": str(intent.pk),
            "idempotency_key": intent.idempotency_key,
            "account_partition": intent.account_partition,
            "created_at": intent.created_at.isoformat(),
        }, maxlen=getattr(settings, "ORDER_STREAM_MAXLEN", 200000), approximate=True)
        updated = bool(BrokerOrderIntent.objects.filter(
            pk=intent.pk, status=BrokerOrderIntent.STATUS_RESERVED,
        ).update(
            status=BrokerOrderIntent.STATUS_PUBLISHED, stream_name=target,
            stream_message_id=message_id, published_at=timezone.now(), updated_at=timezone.now(),
            lifecycle_state=(
                BrokerOrderIntent.LIFECYCLE_QUEUED
                if intent.kind == BrokerOrderIntent.KIND_EXIT else intent.lifecycle_state
            ),
        ))
        if not updated:
            logger.info("Intent %s reached a terminal state while publication was completing", intent.pk)
        return message_id
    finally:
        # If the DB update was not durable, retain the short lease. That avoids
        # an immediate duplicate XADD; the outbox retries after lease expiry.
        if updated:
            client.eval(
                "if redis.call('get',KEYS[1])==ARGV[1] then return redis.call('del',KEYS[1]) end return 0",
                1, lock_key, owner,
            )


def publish_intents_batch(intent_ids: list[int]) -> int:
    """Pipeline Stream publication and persist publication state in one DB write."""
    if not intent_ids:
        return 0
    intents = list(BrokerOrderIntent.objects.filter(
        pk__in=intent_ids, status=BrokerOrderIntent.STATUS_RESERVED,
    ).order_by("pk"))
    if not intents:
        return 0
    client = redis_client()
    owners = {intent.pk: uuid.uuid4().hex for intent in intents}
    locks = client.pipeline(transaction=False)
    for intent in intents:
        locks.set(f"orders:publish:lock:{intent.pk}", owners[intent.pk], nx=True, ex=30)
    acquired_flags = locks.execute()
    acquired = [intent for intent, flag in zip(intents, acquired_flags) if flag]
    if not acquired:
        return 0
    publisher = client.pipeline(transaction=False)
    maxlen = getattr(settings, "ORDER_STREAM_MAXLEN", 200000)
    for intent in acquired:
        publisher.xadd(stream_name(broker=intent.broker, kind=intent.kind), {
            "intent_id": str(intent.pk),
            "idempotency_key": intent.idempotency_key,
            "account_partition": intent.account_partition,
            "created_at": intent.created_at.isoformat(),
        }, maxlen=maxlen, approximate=True)
    message_ids = publisher.execute()
    published_at = timezone.now()
    messages = {intent.pk: str(message_id) for intent, message_id in zip(acquired, message_ids)}
    streams = {intent.pk: stream_name(broker=intent.broker, kind=intent.kind) for intent in acquired}
    updated = False
    try:
        with transaction.atomic():
            # A fast gateway may acknowledge after XADD but before this write.
            # The status predicate prevents publication metadata from moving a
            # terminal/submitting intent backwards to PUBLISHED.
            for offset in range(0, len(acquired), 500):
                chunk = acquired[offset:offset + 500]
                BrokerOrderIntent.objects.filter(
                    pk__in=[intent.pk for intent in chunk],
                    status=BrokerOrderIntent.STATUS_RESERVED,
                ).update(
                    status=BrokerOrderIntent.STATUS_PUBLISHED,
                    lifecycle_state=Case(*[
                        When(pk=intent.pk, kind=BrokerOrderIntent.KIND_EXIT,
                             then=Value(BrokerOrderIntent.LIFECYCLE_QUEUED))
                        for intent in chunk
                    ], default=Value(BrokerOrderIntent.LIFECYCLE_QUEUED), output_field=CharField()),
                    stream_name=Case(*[
                        When(pk=intent.pk, then=Value(streams[intent.pk]))
                        for intent in chunk
                    ], output_field=CharField()),
                    stream_message_id=Case(*[
                        When(pk=intent.pk, then=Value(messages[intent.pk]))
                        for intent in chunk
                    ], output_field=CharField()),
                    published_at=published_at,
                    updated_at=published_at,
                )
        updated = True
        return len(acquired)
    finally:
        if updated:
            release = client.pipeline(transaction=False)
            script = "if redis.call('get',KEYS[1])==ARGV[1] then return redis.call('del',KEYS[1]) end return 0"
            for intent in acquired:
                release.eval(script, 1, f"orders:publish:lock:{intent.pk}", owners[intent.pk])
            release.execute()


def republish_outbox(*, limit: int = 1000, broker: str | None = None,
                     kind: str | None = None) -> int:
    # This function runs repeatedly inside long-lived gateway executor threads.
    # Django's request-finished hook does not run there, so without explicit
    # cleanup every executor thread can retain one PostgreSQL connection until
    # max_connections is exhausted.
    close_old_connections()
    try:
        pending = BrokerOrderIntent.objects.filter(status=BrokerOrderIntent.STATUS_RESERVED)
        if broker:
            pending = pending.filter(broker=normalize_broker_name(broker))
        if kind:
            pending = pending.filter(kind=kind)
        ids = list(pending.order_by("created_at").values_list("id", flat=True)[:limit])
        try:
            return publish_intents_batch(ids)
        except Exception:
            logger.exception("Order intent outbox batch publication failed count=%s", len(ids))
            return 0
    finally:
        connections.close_all()


def claim_for_submission(intent_id: int, consumer: str) -> BrokerOrderIntent | None:
    """Durable point-of-call idempotency; stalled SUBMITTING is never blind-retried."""
    with transaction.atomic():
        intent = BrokerOrderIntent.objects.select_for_update().filter(pk=intent_id).first()
        if not intent or intent.status in TERMINAL:
            return None
        if intent.status == BrokerOrderIntent.STATUS_SUBMITTING:
            intent.status = BrokerOrderIntent.STATUS_AMBIGUOUS
            intent.last_error = "Gateway ownership was lost after submission began; broker reconciliation required."
            intent.reconcile_after = timezone.now()
            intent.save(update_fields=["status", "last_error", "reconcile_after", "updated_at"])
            return None
        if intent.status not in {BrokerOrderIntent.STATUS_PUBLISHED, BrokerOrderIntent.STATUS_RESERVED}:
            return None
        # A consumer group distributes messages across replicas, so Redis does
        # not itself guarantee account FIFO. Refuse a later account intent until
        # every earlier intent for that account reaches a terminal state.
        earlier_exists = BrokerOrderIntent.objects.filter(
            account_partition=intent.account_partition,
            created_at__lt=intent.created_at,
        ).exclude(status__in=TERMINAL).exists()
        if earlier_exists:
            return None
        intent.status = BrokerOrderIntent.STATUS_SUBMITTING
        intent.lifecycle_state = BrokerOrderIntent.LIFECYCLE_SUBMITTING
        intent.consumer = consumer
        intent.owner_token = consumer
        intent.fencing_token += 1
        intent.heartbeat_at = timezone.now()
        intent.submission_started_at = timezone.now()
        intent.attempt_count += 1
        intent.save(update_fields=[
            "status", "lifecycle_state", "consumer", "owner_token", "fencing_token",
            "heartbeat_at", "submission_started_at", "attempt_count", "updated_at",
        ])
        if intent.published_at:
            queue_ms = (intent.submission_started_at - intent.published_at).total_seconds() * 1000
            if queue_ms > 2000:
                warning_key = f"{intent.broker}:{intent.kind}"
                now = time.monotonic()
                with _QUEUE_WARNING_LOCK:
                    previous = _QUEUE_WARNING_LAST.get(warning_key, 0.0)
                    should_warn = now - previous >= 5.0
                    if should_warn:
                        _QUEUE_WARNING_LAST[warning_key] = now
                if should_warn:
                    logger.warning(
                        "Order Stream queue-to-broker threshold exceeded intent_id=%s broker=%s kind=%s queue_ms=%.0f "
                        "(equivalent warnings suppressed for 5s)",
                        intent.pk, intent.broker, intent.kind, queue_ms,
                    )
        return intent


def record_outcome(intent_id: int, *, status: str, outcome: dict | None = None,
                   error: str = "", reconcile_delay: int = 5) -> None:
    values = {"status": status, "outcome": outcome or {}, "last_error": error, "updated_at": timezone.now()}
    data = outcome or {}
    values["broker_order_id"] = str(data.get("order_id") or data.get("orderid") or "")
    values["broker_status"] = str(data.get("status") or "")
    if status == BrokerOrderIntent.STATUS_ACKNOWLEDGED:
        values["acknowledged_at"] = timezone.now()
        raw_status = str(data.get("status") or "").strip().casefold()
        filled = data.get("filled_quantity") or data.get("filled_qty") or 0
        requested = data.get("quantity") or data.get("requested_quantity") or 0
        try:
            filled = max(int(float(filled or 0)), 0)
            requested = max(int(float(requested or 0)), 0)
        except (TypeError, ValueError):
            filled = requested = 0
        if raw_status in {"complete", "completed", "filled", "executed", "traded", "success", "reconciled_closed"}:
            values["lifecycle_state"] = BrokerOrderIntent.LIFECYCLE_FILLED
            values["filled_at"] = timezone.now()
        elif filled > 0 and (not requested or filled < requested):
            values["lifecycle_state"] = BrokerOrderIntent.LIFECYCLE_PARTIAL
        else:
            values["lifecycle_state"] = BrokerOrderIntent.LIFECYCLE_BROKER_ACCEPTED
            values["broker_accepted_at"] = timezone.now()
        if filled:
            values["filled_quantity"] = filled
            # F() is intentionally avoided here because outcome may contain
            # the broker's cumulative fill quantity rather than a delta.
            intent = BrokerOrderIntent.objects.filter(pk=intent_id).only("requested_quantity").first()
            requested_total = int(getattr(intent, "requested_quantity", 0) or requested or filled)
            values["remaining_quantity"] = max(requested_total - filled, 0)
    if status in {BrokerOrderIntent.STATUS_AMBIGUOUS, BrokerOrderIntent.STATUS_RECONCILING}:
        values["reconcile_after"] = timezone.now() + timedelta(seconds=reconcile_delay)
        values["lifecycle_state"] = BrokerOrderIntent.LIFECYCLE_UNCERTAIN
    if status == BrokerOrderIntent.STATUS_REJECTED:
        values["lifecycle_state"] = BrokerOrderIntent.LIFECYCLE_ATTENTION
    BrokerOrderIntent.objects.filter(pk=intent_id).update(**values)


def partition_number(account_partition: str, partitions: int) -> int:
    digest = hashlib.sha256(account_partition.encode()).digest()
    return int.from_bytes(digest[:8], "big") % max(1, partitions)


def result_fields(intent: BrokerOrderIntent) -> dict[str, str]:
    return {"intent_id": str(intent.pk), "status": intent.status, "broker": intent.broker,
            "kind": intent.kind, "at": timezone.now().isoformat()}
