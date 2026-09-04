"""Cached broker-session readiness checks outside latency-sensitive BUY workers."""

from __future__ import annotations

import logging
from typing import Any

from django.core.cache import cache
from django.utils import timezone

from main.broker_registry import normalize_broker_name
from main.services.execution_nodes import ensure_broker_execution_node

logger = logging.getLogger("main")
READY_TTL_SECONDS = 45 * 60


def readiness_key(broker_details_id: int) -> str:
    return f"entry:broker-session-readiness:v1:{int(broker_details_id)}"


def get_cached_readiness(broker_details_id: int) -> dict[str, Any] | None:
    value = cache.get(readiness_key(broker_details_id))
    return value if isinstance(value, dict) else None


def _save(details, *, status: str, reason: str, remote_verified: bool = False) -> dict[str, Any]:
    payload = {
        "broker_details_id": details.id,
        "client_id": details.client_id,
        "broker": normalize_broker_name(getattr(details.broker_name, "broker_name", "")),
        "status": status,
        "reason": reason,
        "remote_verified": remote_verified,
        "checked_at": timezone.now().isoformat(),
    }
    cache.set(readiness_key(details.id), payload, timeout=READY_TTL_SECONDS)
    return payload


def validate_broker_session(details, *, verify_remote: bool = False) -> dict[str, Any]:
    """Validate durable credentials/node state without ever placing an order."""
    broker = normalize_broker_name(getattr(details.broker_name, "broker_name", ""))
    if broker == "demo broker":
        return _save(details, status="READY", reason="Demo Broker requires no session.", remote_verified=True)
    service_error = details.client.service_access_error()
    if service_error:
        return _save(details, status="INVALID", reason=service_error)
    if not details.client.is_enable:
        return _save(details, status="INVALID", reason="Client Trading Status is OFF.")
    token = details.get_access_token_secure() if details.is_angel_one_broker() else details.access_token
    if not str(token or "").strip():
        return _save(details, status="INVALID", reason=f"{broker.title()} session token is missing—reconnect broker.")
    if details.isTokenExpired:
        return _save(details, status="INVALID", reason=f"{broker.title()} session is marked expired—reconnect broker.")
    expiry = details.access_token_expiry
    if expiry:
        if timezone.is_naive(expiry):
            expiry = timezone.make_aware(expiry)
        if expiry <= timezone.now():
            return _save(details, status="INVALID", reason=f"{broker.title()} session token has expired—reconnect broker.")
    if not ensure_broker_execution_node(details):
        return _save(details, status="INVALID", reason="Verified execution IP/node is not assigned.")
    # Remote broker calls are deliberately excluded from the dispatch path.
    # The adapter performs authoritative validation when the order is submitted.
    return _save(
        details,
        status="READY_LOCAL",
        reason="Token and execution-node readiness passed.",
        remote_verified=False,
    )
