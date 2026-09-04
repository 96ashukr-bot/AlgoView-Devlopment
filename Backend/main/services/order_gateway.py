"""Gateway execution primitives shared by the async management command and tests."""

from __future__ import annotations

from contextlib import contextmanager
import time
from django.conf import settings

from main.models import BrokerOrderIntent

TOKEN_BUCKET_LUA = """
local now=tonumber(ARGV[1]); local rate=tonumber(ARGV[2]); local burst=tonumber(ARGV[3])
local data=redis.call('HMGET',KEYS[1],'tokens','ts')
local tokens=tonumber(data[1]) or burst; local ts=tonumber(data[2]) or now
tokens=math.min(burst,tokens+math.max(0,now-ts)*rate)
if tokens < 1 then redis.call('HMSET',KEYS[1],'tokens',tokens,'ts',now); redis.call('EXPIRE',KEYS[1],60); return 0 end
redis.call('HMSET',KEYS[1],'tokens',tokens-1,'ts',now); redis.call('EXPIRE',KEYS[1],60); return 1
"""


def rate_dimensions(intent: BrokerOrderIntent) -> list[str]:
    payload = intent.payload or {}
    values = [f"account:{intent.account_partition}"]
    for name in ("api_app_id", "execution_node_id", "outbound_ip_id"):
        if payload.get(name):
            values.append(f"{name}:{payload[name]}")
    return values


def acquire_rate_capacity(client, intent: BrokerOrderIntent, now: float) -> bool:
    limits = getattr(settings, "ORDER_STREAM_RATE_LIMITS", {}) or {}
    broker = intent.broker.casefold()
    config = limits.get(broker, {"rate": 8.0, "burst": 8})
    for dimension in rate_dimensions(intent):
        allowed = client.eval(TOKEN_BUCKET_LUA, 1, f"orders:rate:{broker}:{dimension}", now,
                              float(config.get("rate", 8.0)), int(config.get("burst", 8)))
        if not allowed:
            return False
    return True


@contextmanager
def account_sequence_lock(client, intent: BrokerOrderIntent, owner: str, ttl_ms: int = 30000, wait_seconds: float = 5.0):
    key = f"orders:fifo:{intent.account_partition}"
    deadline = time.monotonic() + max(0, wait_seconds)
    acquired = False
    while not acquired:
        acquired = bool(client.set(key, owner, nx=True, px=ttl_ms))
        if acquired or time.monotonic() >= deadline:
            break
        time.sleep(0.01)
    try:
        yield acquired
    finally:
        if acquired:
            client.eval("if redis.call('get',KEYS[1])==ARGV[1] then return redis.call('del',KEYS[1]) end return 0", 1, key, owner)


def execute_intent(intent: BrokerOrderIntent):
    """Resolve credentials at execution time; Stream payload contains references only."""
    if getattr(settings, "ORDER_STREAM_SHADOW_MODE", True):
        return {"status": "shadow", "message": "Validated without broker submission"}
    if intent.source_type == "manual_trade_result":
        from main.manual_trade_service import _execute_manual_trade_result
        from main.models import ManualTradeResult
        _execute_manual_trade_result(int(intent.source_id))
        row = ManualTradeResult.objects.filter(pk=int(intent.source_id)).first()
        if row is None:
            raise RuntimeError("Manual trade result disappeared during gateway execution")
        return {
            "status": "failed" if row.status == ManualTradeResult.STATUS_FAILED else (row.broker_status or row.status),
            "order_id": row.order_id or "", "message": row.reason or "",
            "source_id": intent.source_id,
        }
    if intent.source_type == "webhook_trade":
        from main.tasks import process_single_webhook_trade_task
        payload = intent.payload or {}
        context = dict(payload.get("context") or {})
        context["broker_order_intent_id"] = intent.id
        return process_single_webhook_trade_task.run(
            trade_id=int(intent.source_id), index=int(payload.get("index", 1)),
            context=context, history_mode=payload.get("history_mode", "default"),
            entry_order_key=intent.idempotency_key, entry_account_key=intent.account_partition,
        )
    if intent.source_type == "sltp_exit":
        from main.tasks import process_sltp_exit_task
        payload = intent.payload or {}
        return process_sltp_exit_task.run(
            trade_history_id=int(intent.source_id), dispatch_token=payload["dispatch_token"],
            trigger_snapshot=payload.get("trigger_snapshot") or {}, exit_intent_id=intent.id,
        )
    if intent.source_type == "kill_switch_exit":
        from main.tasks import force_kill_switch_trade_task
        payload = intent.payload or {}
        return force_kill_switch_trade_task.run(
            trade_history_id=int(intent.source_id), reason=payload.get("reason", ""),
            initiated_by_id=payload.get("initiated_by_id"), dispatch_token=payload.get("dispatch_token"),
            captured_ltp=payload.get("captured_ltp"), captured_at=payload.get("captured_at"),
            exit_intent_id=intent.id,
        )
    raise ValueError(f"Unsupported order intent source: {intent.source_type}")
