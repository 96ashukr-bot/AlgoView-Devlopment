from __future__ import annotations

import hashlib
import hmac
import json
import time
from typing import Any

from django.conf import settings
from django.core.exceptions import PermissionDenied, ValidationError


def canonical_payload(payload: Any) -> str:
    return json.dumps(payload or {}, sort_keys=True, separators=(",", ":"), default=str)


def generate_node_signature(secret: str, timestamp: str, payload: Any) -> str:
    body = f"{timestamp}.{canonical_payload(payload)}"
    return hmac.new(str(secret or "").encode(), body.encode(), hashlib.sha256).hexdigest()


def verify_node_signature(secret: str, timestamp: str, payload: Any, signature: str, *, max_skew_seconds: int | None = None) -> None:
    if not secret:
        raise ValidationError("Node secret is not configured.")
    if not timestamp or not signature:
        raise PermissionDenied("Missing node signature headers.")
    try:
        request_ts = int(timestamp)
    except (TypeError, ValueError):
        raise PermissionDenied("Invalid node timestamp.")

    skew = int(max_skew_seconds if max_skew_seconds is not None else settings.NODE_ALLOWED_CLOCK_SKEW_SECONDS)
    if abs(int(time.time()) - request_ts) > skew:
        raise PermissionDenied("Node request timestamp is outside allowed skew.")

    expected = generate_node_signature(secret, str(timestamp), payload)
    if not hmac.compare_digest(expected, str(signature)):
        raise PermissionDenied("Invalid node request signature.")
