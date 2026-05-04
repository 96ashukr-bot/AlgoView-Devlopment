"""
Secret redaction helpers for logs and API-safe payloads.
"""

from __future__ import annotations

import re
from typing import Any


SENSITIVE_KEYS = {
    "access_token",
    "auth_token",
    "jwtToken",
    "jwt_token",
    "refresh_token",
    "refreshToken",
    "feed_token",
    "feedToken",
    "password",
    "broker_pass",
    "totp",
    "totp_secret",
    "broker_Totp_Authcode",
    "api_key",
    "app_id",
    "broker_API_KEY",
    "api_secret",
    "app_secret",
    "broker_API_SKEY",
    "authorization",
    "Authorization",
}

SENSITIVE_QUERY_PARAMS = (
    "access_token",
    "auth_token",
    "jwtToken",
    "refresh_token",
    "refreshToken",
    "feed_token",
    "feedToken",
    "code",
    "auth_code",
    "authCode",
    "api_key",
    "app_id",
    "app_secret",
    "request_token",
    "RequestToken",
    "tokenId",
    "token_id",
)


def redact_value(value: Any) -> str:
    if value in (None, ""):
        return ""
    return "***REDACTED***"


def redact_secrets(payload: Any) -> Any:
    if isinstance(payload, dict):
        return {
            key: redact_value(value) if key in SENSITIVE_KEYS else redact_secrets(value)
            for key, value in payload.items()
        }
    if isinstance(payload, list):
        return [redact_secrets(item) for item in payload]
    if isinstance(payload, tuple):
        return tuple(redact_secrets(item) for item in payload)
    return payload


def sanitize_text(value: Any) -> Any:
    if not isinstance(value, str):
        return value

    sanitized = value
    for key in SENSITIVE_QUERY_PARAMS:
        sanitized = re.sub(rf"([?&]{re.escape(key)}=)[^&\\s]+", rf"\1***REDACTED***", sanitized)

    sanitized = re.sub(
        r"(access_token|auth_token|jwtToken|refresh_token|refreshToken|feed_token|feedToken|auth_code|authCode|code|api_key|app_id|app_secret|request_token|RequestToken|tokenId|token_id)=([^&\s]+)",
        r"\1=***REDACTED***",
        sanitized,
    )
    return sanitized
