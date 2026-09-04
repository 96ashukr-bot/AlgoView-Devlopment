"""Atomic duplicate reservation, account FIFO and per-account token buckets."""

from __future__ import annotations

import hashlib
import json
import logging
import threading
import time
from contextlib import contextmanager

from django.conf import settings
from django.core.cache import cache
from django.db import connection

logger = logging.getLogger("main")

DEFAULT_ACCOUNT_RATE = 8.0
DEFAULT_ACCOUNT_BURST = 3
# Broker tasks have a hard limit of 300 seconds. Keep the Redis lease beyond
# that boundary so a slow/uncertain broker submission cannot overlap a second
# SELL for the same account after the old 90-second lease expired.
ACCOUNT_LOCK_TTL_SECONDS = 360
EXIT_PENDING_TTL_SECONDS = 180
ENTRY_TURN_WAIT_SECONDS = 0.25
EXIT_TURN_WAIT_SECONDS = 0.25


class EntryAccountTurnDeferred(RuntimeError):
    """The account's earlier order/priority exit must run before this entry."""


class ExitAccountTurnDeferred(RuntimeError):
    """An earlier risk-reducing order still owns this account's exit turn."""


def account_key(broker, client_id) -> str:
    safe_broker = "".join(ch for ch in str(broker or "unknown").casefold() if ch.isalnum()) or "unknown"
    return f"{safe_broker}:{int(client_id)}"


def reserve_entry(order_key: str, timeout: int = 600) -> bool:
    digest = hashlib.sha256(str(order_key).encode("utf-8")).hexdigest()
    return bool(cache.add(f"entry:duplicate:{digest}", "1", timeout=timeout))


def enqueue_account_order(*, broker: str, client_id: int, order_key: str) -> bool:
    """Place an order in its account FIFO at publication time."""
    client = _redis_client()
    if client is None:
        return False
    scope = account_key(broker, client_id)
    queue_key = f"entry:fifo:{scope}"
    marker_key = f"entry:fifo:item:{hashlib.sha256(order_key.encode()).hexdigest()}"
    token = json.dumps({"key": order_key}, separators=(",", ":"))
    try:
        if not client.set(marker_key, token, nx=True, ex=120):
            return True
        pipe = client.pipeline(transaction=True)
        pipe.rpush(queue_key, token)
        pipe.expire(queue_key, 180)
        pipe.execute()
        return True
    except Exception:
        logger.exception("Could not enqueue Redis account FIFO item")
        return False


def enqueue_exit_account_order(*, broker: str, client_id: int, order_key: str) -> bool:
    """Advertise an exit before publication so new entries yield to it."""
    client = _redis_client()
    if client is None:
        return False
    scope = account_key(broker, client_id)
    queue_key = f"exit:fifo:{scope}"
    marker_key = f"exit:fifo:item:{hashlib.sha256(order_key.encode()).hexdigest()}"
    token = json.dumps({"key": order_key}, separators=(",", ":"))
    try:
        if not client.set(marker_key, token, nx=True, ex=EXIT_PENDING_TTL_SECONDS):
            return True
        pipe = client.pipeline(transaction=True)
        pipe.rpush(queue_key, token)
        pipe.expire(queue_key, EXIT_PENDING_TTL_SECONDS)
        pipe.set(f"exit:pending:{scope}", "1", ex=EXIT_PENDING_TTL_SECONDS)
        pipe.execute()
        return True
    except Exception:
        logger.exception("Could not enqueue Redis priority-exit item")
        return False


def _acquire_execution_lock(client, scope: str, token: str, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    key = f"account:execution-lock:{scope}"
    while time.monotonic() < deadline:
        if client.set(key, token, nx=True, ex=ACCOUNT_LOCK_TTL_SECONDS):
            return True
        time.sleep(0.01)
    return False


def _release_execution_lock(client, scope: str, token: str) -> None:
    key = f"account:execution-lock:{scope}"
    try:
        if client.get(key) == token:
            client.delete(key)
    except Exception:
        logger.exception("Could not release account execution lock")


def _redis_client():
    redis_url = str(getattr(settings, "REDIS_URL", "") or "").strip()
    if not redis_url:
        return None
    try:
        import redis

        return redis.Redis.from_url(redis_url, decode_responses=True, socket_timeout=2)
    except Exception:
        logger.exception("Redis entry-control client could not be created")
        return None


_LOCAL_ACCOUNT_LOCKS: dict[str, threading.Lock] = {}
_LOCAL_ACCOUNT_LOCKS_GUARD = threading.Lock()


@contextmanager
def _durable_account_turn(*, broker: str, client_id: int, timeout: float):
    """Serialize an account when Redis is unavailable.

    PostgreSQL advisory locks coordinate every application instance. The
    process-local lock keeps development/test databases deterministic.
    """
    scope = account_key(broker, client_id)
    if connection.vendor == "postgresql":
        lock_id = int.from_bytes(hashlib.sha256(scope.encode()).digest()[:8], "big", signed=True)
        deadline = time.monotonic() + max(timeout, 0.1)
        acquired = False
        try:
            while time.monotonic() < deadline:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_try_advisory_lock(%s)", [lock_id])
                    acquired = bool(cursor.fetchone()[0])
                if acquired:
                    break
                time.sleep(0.01)
            if not acquired:
                raise ExitAccountTurnDeferred("Another priority exit is currently executing for this account.")
            yield
        finally:
            if acquired:
                with connection.cursor() as cursor:
                    cursor.execute("SELECT pg_advisory_unlock(%s)", [lock_id])
        return
    with _LOCAL_ACCOUNT_LOCKS_GUARD:
        lock = _LOCAL_ACCOUNT_LOCKS.setdefault(scope, threading.Lock())
    acquired = lock.acquire(timeout=max(timeout, 0.1))
    if not acquired:
        raise ExitAccountTurnDeferred("Another priority exit is currently executing for this account.")
    try:
        yield
    finally:
        lock.release()


@contextmanager
def noncritical_account_turn(*, broker: str, client_id: int, timeout: float = 0.02):
    """Reserve an account briefly for a background broker read.

    Static proxy subscriptions can reject overlapping CONNECT tunnels even
    when each individual credential is valid. Background readiness/position
    traffic must therefore share the live order execution lock, while always
    yielding to queued entries and exits. The yielded value is False when the
    caller should skip/defer its non-critical request.
    """
    client = _redis_client()
    if client is None:
        yield True
        return
    scope = account_key(broker, client_id)
    entry_queue_key = f"entry:fifo:{scope}"
    exit_pending_key = f"exit:pending:{scope}"
    lock_token = hashlib.sha256(f"background:{scope}:{time.time_ns()}".encode()).hexdigest()
    acquired = False
    allowed = False
    try:
        if client.exists(exit_pending_key) or client.llen(entry_queue_key):
            yield False
            return
        acquired = _acquire_execution_lock(client, scope, lock_token, max(0.01, timeout))
        if not acquired:
            yield False
            return
        # Close the race between the initial queue check and lock acquisition.
        if client.exists(exit_pending_key) or client.llen(entry_queue_key):
            yield False
            return
        allowed = True
        yield True
    finally:
        if client is not None and acquired:
            _release_execution_lock(client, scope, lock_token)


def _rate_settings(broker: str) -> tuple[float, int]:
    configured = getattr(settings, "ENTRY_BROKER_ACCOUNT_RATE_LIMITS", {}) or {}
    value = configured.get(str(broker or "").strip().casefold(), {}) if isinstance(configured, dict) else {}
    return float(value.get("rate", DEFAULT_ACCOUNT_RATE)), int(value.get("burst", DEFAULT_ACCOUNT_BURST))


@contextmanager
def account_fifo_turn(
    *, broker: str, client_id: int, order_key: str, timeout: float = ENTRY_TURN_WAIT_SECONDS
):
    """Serialize entries without allowing an out-of-turn task to occupy a worker."""
    client = _redis_client()
    if client is None:
        with _durable_account_turn(broker=broker, client_id=client_id, timeout=timeout):
            yield
        return
    scope = account_key(broker, client_id)
    queue_key = f"entry:fifo:{scope}"
    marker_key = f"entry:fifo:item:{hashlib.sha256(order_key.encode()).hexdigest()}"
    token = json.dumps({"key": order_key}, separators=(",", ":"))
    controlled = False
    lock_token = hashlib.sha256(f"entry:{order_key}:{time.time_ns()}".encode()).hexdigest()
    lock_acquired = False
    try:
        if not client.exists(marker_key):
            enqueue_account_order(broker=broker, client_id=client_id, order_key=order_key)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            # An already-running entry cannot be interrupted safely, but no
            # new BUY may start while a risk-reducing exit is pending.
            if client.exists(f"exit:pending:{scope}"):
                time.sleep(0.02)
                continue
            head = client.lindex(queue_key, 0)
            if head == token:
                break
            if head:
                try:
                    head_key = json.loads(head).get("key", "")
                    head_marker = f"entry:fifo:item:{hashlib.sha256(head_key.encode()).hexdigest()}"
                    if not client.exists(head_marker):
                        client.lpop(queue_key)
                        continue
                except Exception:
                    pass
            time.sleep(0.02)
        else:
            raise EntryAccountTurnDeferred("An earlier account order or priority exit is still pending.")

        lock_acquired = _acquire_execution_lock(client, scope, lock_token, max(0.1, deadline - time.monotonic()))
        if not lock_acquired:
            raise EntryAccountTurnDeferred("Another order is currently executing for this account.")
        if client.exists(f"exit:pending:{scope}"):
            _release_execution_lock(client, scope, lock_token)
            lock_acquired = False
            raise EntryAccountTurnDeferred("Entry yielded because a priority exit is pending.")

        rate, burst = _rate_settings(broker)
        rate_key = f"entry:rate:{scope}"
        while True:
            now = time.time()
            window = int(now)
            current = client.incr(f"{rate_key}:{window}")
            if current == 1:
                client.expire(f"{rate_key}:{window}", 2)
            if current <= max(burst, int(rate)):
                break
            time.sleep(min(0.05, max(0.005, (window + 1) - now)))
        controlled = True
    except EntryAccountTurnDeferred:
        # This is expected during bursts. The Celery task is retried without
        # tying up a broker worker thread, allowing the FIFO head to run.
        raise
    except Exception:
        logger.exception("Redis FIFO/rate control failed; durable execution safeguards remain authoritative")
    try:
        yield
    finally:
        try:
            if client is not None and lock_acquired:
                _release_execution_lock(client, scope, lock_token)
            if client is not None and controlled:
                if client.lindex(queue_key, 0) == token:
                    client.lpop(queue_key)
                else:
                    client.lrem(queue_key, 1, token)
                client.delete(marker_key)
        except Exception:
            logger.exception("Could not release Redis entry FIFO turn")


@contextmanager
def exit_account_turn(
    *, broker: str, client_id: int, order_key: str, timeout: float = EXIT_TURN_WAIT_SECONDS
):
    """Serialize exits without occupying a broker worker while waiting.

    Contention is deliberately reported quickly to the caller. Celery can
    then retry the task outside the worker process instead of holding scarce
    exit capacity for 30 seconds and incorrectly recording a pre-broker
    failure.
    """
    # Demo Broker has no remote account, rate limit, position race, or broker
    # session. Serialising simulated exits only makes unrelated symbols block
    # each other during a webhook burst.
    if account_key(broker, client_id).startswith("demobroker:"):
        yield
        return
    client = _redis_client()
    if client is None:
        with _durable_account_turn(broker=broker, client_id=client_id, timeout=timeout):
            yield
        return
    scope = account_key(broker, client_id)
    queue_key = f"exit:fifo:{scope}"
    marker_key = f"exit:fifo:item:{hashlib.sha256(order_key.encode()).hexdigest()}"
    token = json.dumps({"key": order_key}, separators=(",", ":"))
    lock_token = hashlib.sha256(f"exit:{order_key}:{time.time_ns()}".encode()).hexdigest()
    controlled = False
    lock_acquired = False
    redis_failed = False
    try:
        if not client.exists(marker_key):
            enqueue_exit_account_order(broker=broker, client_id=client_id, order_key=order_key)
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            head = client.lindex(queue_key, 0)
            if head == token:
                break
            if head:
                try:
                    head_key = json.loads(head).get("key", "")
                    stale_marker = f"exit:fifo:item:{hashlib.sha256(head_key.encode()).hexdigest()}"
                    if not client.exists(stale_marker):
                        client.lpop(queue_key)
                        continue
                except Exception:
                    pass
            time.sleep(0.01)
        else:
            raise ExitAccountTurnDeferred("An earlier priority exit is still pending for this account.")
        lock_acquired = _acquire_execution_lock(client, scope, lock_token, max(0.1, deadline - time.monotonic()))
        if not lock_acquired:
            raise ExitAccountTurnDeferred("Another priority exit is currently executing for this account.")
        controlled = True
    except ExitAccountTurnDeferred:
        logger.info("Priority exit account turn deferred scope=%s order_key=%s", scope, order_key)
        raise
    except Exception as exc:
        logger.exception("Redis priority-exit control failed; durable broker safeguards remain authoritative")
        redis_failed = True
    if redis_failed:
        with _durable_account_turn(broker=broker, client_id=client_id, timeout=timeout):
            yield
        return
    try:
        yield
    finally:
        try:
            if lock_acquired:
                _release_execution_lock(client, scope, lock_token)
            if controlled:
                if client.lindex(queue_key, 0) == token:
                    client.lpop(queue_key)
                else:
                    client.lrem(queue_key, 1, token)
                client.delete(marker_key)
                if client.llen(queue_key) == 0:
                    client.delete(f"exit:pending:{scope}")
        except Exception:
            logger.exception("Could not release Redis priority-exit turn")
