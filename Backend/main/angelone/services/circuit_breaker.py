"""
Redis-backed circuit breaker for broker auth instability.
"""

from __future__ import annotations

import threading
from datetime import timedelta

from django.conf import settings
from django.core.cache import caches
from django.utils import timezone


class BrokerAuthCircuitBreaker:
    _fallback_lock = threading.Lock()
    _fallback_store = {}

    def __init__(self, broker_name: str = "angelone"):
        self._cache = caches["circuit_breaker"]
        prefix = settings.ANGELONE_CIRCUIT_CACHE_PREFIX
        self._failures_key = f"{prefix}:{broker_name}:failures"
        self._open_key = f"{prefix}:{broker_name}:open"
        self._threshold = settings.ANGELONE_CIRCUIT_BREAKER_FAILURE_THRESHOLD
        self._recovery_seconds = settings.ANGELONE_CIRCUIT_BREAKER_RECOVERY_SECONDS

    def _fallback_get(self, key):
        with self._fallback_lock:
            record = self._fallback_store.get(key)
            if not record:
                return None
            if record["expires_at"] <= timezone.now():
                self._fallback_store.pop(key, None)
                return None
            return record["value"]

    def _fallback_set(self, key, value):
        with self._fallback_lock:
            self._fallback_store[key] = {
                "value": value,
                "expires_at": timezone.now() + timedelta(seconds=self._recovery_seconds),
            }

    def _fallback_delete_many(self, keys):
        with self._fallback_lock:
            for key in keys:
                self._fallback_store.pop(key, None)

    def is_open(self) -> bool:
        try:
            return bool(self._cache.get(self._open_key))
        except Exception:
            return bool(self._fallback_get(self._open_key))

    def record_success(self) -> None:
        try:
            self._cache.delete_many([self._failures_key, self._open_key])
        except Exception:
            self._fallback_delete_many([self._failures_key, self._open_key])

    def record_failure(self) -> None:
        try:
            failures = self._cache.get(self._failures_key, 0) + 1
            self._cache.set(self._failures_key, failures, timeout=self._recovery_seconds)
            if failures >= self._threshold:
                self._cache.set(self._open_key, True, timeout=self._recovery_seconds)
            return
        except Exception:
            failures = (self._fallback_get(self._failures_key) or 0) + 1
            self._fallback_set(self._failures_key, failures)
        if failures >= self._threshold:
            self._fallback_set(self._open_key, True)
