"""
Encryption helpers for broker secrets and tokens.
"""

from __future__ import annotations

from typing import List, Optional

from cryptography.fernet import Fernet, InvalidToken, MultiFernet
from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def _get_configured_keys() -> List[str]:
    configured = [item.strip() for item in getattr(settings, "BROKER_ENCRYPTION_KEYS", "").split(",") if item.strip()]
    if configured:
        return configured
    raise ImproperlyConfigured("BROKER_ENCRYPTION_KEYS must be configured")


def _get_cipher() -> MultiFernet:
    keys = [Fernet(key.encode("ascii")) for key in _get_configured_keys()]
    return MultiFernet(keys)


def encrypt_value(value: Optional[str]) -> Optional[str]:
    if value in (None, ""):
        return None
    return _get_cipher().encrypt(value.encode("utf-8")).decode("utf-8")


def decrypt_value(value: Optional[str]) -> Optional[str]:
    if value in (None, ""):
        return None
    try:
        return _get_cipher().decrypt(value.encode("utf-8")).decode("utf-8")
    except InvalidToken:
        return None
