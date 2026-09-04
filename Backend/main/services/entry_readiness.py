"""Redis-backed entry matching cache with PostgreSQL as durable fallback."""

from __future__ import annotations

import hashlib
import json
from typing import Callable

from django.core.cache import cache
from django.utils import timezone


VERSION_KEY = "entry:readiness:version:v1"
KEY_REGISTRY = "entry:readiness:keys:v1"
TIMEOUT_SECONDS = 6 * 60 * 60
SNAPSHOT_PREFIX = "entry:readiness:trade:v1:"


def _version() -> int:
    return int(cache.get(VERSION_KEY, 1) or 1)


def invalidate_entry_readiness() -> None:
    """Atomically invalidate cached match sets after any eligibility mutation."""
    cache.add(VERSION_KEY, 1, timeout=None)
    try:
        cache.incr(VERSION_KEY)
    except Exception:
        cache.set(VERSION_KEY, _version() + 1, timeout=None)


def _key(*, company_id, strategy: str, symbol: str) -> str:
    identity = json.dumps(
        [company_id or 0, str(strategy or "").strip().casefold(), str(symbol or "").strip().upper()],
        separators=(",", ":"),
    )
    digest = hashlib.sha256(identity.encode("utf-8")).hexdigest()
    return f"entry:readiness:match:v{_version()}:{digest}"


def get_or_build_match_ids(*, company_id, strategy: str, symbol: str, builder: Callable[[], list[int]]) -> list[int]:
    key = _key(company_id=company_id, strategy=strategy, symbol=symbol)
    cached = cache.get(key)
    if isinstance(cached, list):
        return [int(value) for value in cached]
    trade_ids = [int(value) for value in builder()]
    cache.set(key, trade_ids, timeout=TIMEOUT_SECONDS)
    registry = list(cache.get(KEY_REGISTRY) or [])
    descriptor = {"company_id": company_id, "strategy": strategy, "symbol": symbol}
    if descriptor not in registry:
        registry = (registry + [descriptor])[-1000:]
        cache.set(KEY_REGISTRY, registry, timeout=None)
    return trade_ids


def refresh_trade_snapshots() -> dict:
    """Materialize readiness only for scripts that can receive an entry."""
    from django.db.models import Q
    from main.models import ClientBrokerdetails, ClientTradeSetting

    broker_details = {
        (row.client_id, str(getattr(row.broker_name, "broker_name", "") or "").casefold()): row
        for row in ClientBrokerdetails.objects.select_related("broker_name", "execution_node").all()
    }
    snapshots = {}
    now = timezone.now()
    today = timezone.localdate()
    eligible_trades = (
        ClientTradeSetting.objects.select_related("client", "segment", "sub_segment")
        .filter(client__is_enable=True, is_tread_status=True)
        .filter(Q(client__end_date_client__isnull=True) | Q(client__end_date_client__gte=today))
    )
    for trade in eligible_trades.iterator(chunk_size=500):
        broker_name = str(trade.broker or "").strip()
        detail = broker_details.get((trade.client_id, broker_name.casefold()))
        token_ready = False
        if broker_name.casefold() == "demo broker":
            token_ready = True
        elif detail is not None:
            token_ready = bool(detail.encrypted_access_token or detail.access_token)
            token_ready = token_ready and not bool(detail.isTokenExpired)
            token_ready = token_ready and not bool(detail.access_token_expiry and detail.access_token_expiry <= now)
        snapshots[f"{SNAPSHOT_PREFIX}{trade.id}"] = {
            "trade_setting_id": trade.id,
            "client_id": trade.client_id,
            "company_id": trade.client.white_label_company_id,
            "active_client": bool(trade.client.is_enable),
            "service_active": not bool(trade.client.service_access_error()),
            "trading_status": bool(trade.is_tread_status),
            "strategy": trade.strategy,
            "group_service": trade.group_service,
            "broker": broker_name,
            "broker_detail_id": getattr(detail, "id", None),
            "execution_node_id": getattr(detail, "execution_node_id", None),
            "broker_session_ready": token_ready,
            "quantity": trade.quantity,
            "product_type": trade.product_type,
            "order_type": trade.order_type,
            "symbol": trade.symbol or getattr(trade.sub_segment, "short_name", None) or getattr(trade.sub_segment, "name", None),
            "expiry": trade.expiry_date.isoformat() if trade.expiry_date else None,
            "resolved_contract": {
                "underlying": trade.symbol or getattr(trade.sub_segment, "short_name", None),
                "exchange": getattr(trade.sub_segment, "Exchange", None),
                "expiry": trade.expiry_date.isoformat() if trade.expiry_date else None,
            },
            "refreshed_at": now.isoformat(),
        }
    if snapshots:
        cache.set_many(snapshots, timeout=TIMEOUT_SECONDS)
    # Advance the match-cache generation so bulk database maintenance that
    # bypassed model signals cannot leave an old client set in use.
    invalidate_entry_readiness()
    cache.set("entry:readiness:last_refresh", {"at": now.isoformat(), "count": len(snapshots)}, timeout=TIMEOUT_SECONDS)
    return {"status": "refreshed", "count": len(snapshots), "at": now.isoformat()}


def get_trade_snapshots(trade_ids) -> dict[int, dict]:
    keys = {int(trade_id): f"{SNAPSHOT_PREFIX}{int(trade_id)}" for trade_id in trade_ids}
    values = cache.get_many(keys.values())
    return {trade_id: values[key] for trade_id, key in keys.items() if key in values}
