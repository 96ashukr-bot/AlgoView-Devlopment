"""
One-time callback state storage backed by Redis cache.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

import redis
from django.conf import settings
from django.core.cache import caches
from django.utils import timezone


@dataclass
class CallbackStateRecord:
    state: str
    user_id: int
    broker_details_id: int
    client_code: str
    frontend_redirect_url: Optional[str]
    expires_at: datetime
    created_at: datetime


class CallbackStateService:
    _fallback_lock = threading.Lock()
    _memory_store = {}

    def __init__(self):
        self._cache = caches["default"]
        self._prefix = settings.ANGELONE_STATE_CACHE_PREFIX
        self._ttl = settings.ANGELONE_CALLBACK_STATE_TTL_SECONDS
        self._redis = None
        try:
            if "redis" in self._cache.__class__.__module__.lower():
                candidate = redis.Redis.from_url(settings.REDIS_URL, decode_responses=True, socket_connect_timeout=0.25)
                candidate.ping()
                self._redis = candidate
        except Exception:
            self._redis = None

    def _cache_key(self, state: str) -> str:
        digest = hashlib.sha256(state.encode("utf-8")).hexdigest()
        return f"{self._prefix}:{digest}"

    def create(
        self,
        state: str,
        user_id: int,
        broker_details_id: int,
        client_code: str,
        frontend_redirect_url: Optional[str] = None,
    ) -> CallbackStateRecord:
        now = timezone.now()
        record = {
            "state": state,
            "user_id": user_id,
            "broker_details_id": broker_details_id,
            "client_code": client_code,
            "frontend_redirect_url": frontend_redirect_url,
            "created_at": now.isoformat(),
            "expires_at": (now + timedelta(seconds=self._ttl)).isoformat(),
        }
        key = self._cache_key(state)
        if self._redis:
            self._redis.set(key, json.dumps(record), ex=self._ttl)
        else:
            try:
                self._cache.set(key, record, timeout=self._ttl)
            except Exception:
                with self._fallback_lock:
                    self._memory_store[key] = record
        return self._from_record(record)

    def get(self, state: str) -> Optional[CallbackStateRecord]:
        key = self._cache_key(state)
        record = None
        if self._redis:
            raw = self._redis.get(key)
            record = json.loads(raw) if raw else None
        else:
            try:
                record = self._cache.get(key)
            except Exception:
                with self._fallback_lock:
                    record = self._memory_store.get(key)
        if not record:
            return None
        parsed = self._from_record(record)
        if parsed.expires_at <= timezone.now():
            if self._redis:
                self._redis.delete(key)
            else:
                try:
                    self._cache.delete(key)
                except Exception:
                    with self._fallback_lock:
                        self._memory_store.pop(key, None)
            return None
        return parsed

    def consume(self, state: str) -> Optional[CallbackStateRecord]:
        key = self._cache_key(state)
        record = self._consume_atomic(key)
        if not record:
            return None
        parsed = self._from_record(record)
        if parsed.expires_at <= timezone.now():
            return None
        return parsed

    def _consume_atomic(self, key: str) -> Optional[dict]:
        if self._redis:
            try:
                raw = self._redis.execute_command("GETDEL", key)
            except Exception:
                raw = self._redis.eval(
                    """
                    local val = redis.call('GET', KEYS[1])
                    if val then
                        redis.call('DEL', KEYS[1])
                    end
                    return val
                    """,
                    1,
                    key,
                )
            return json.loads(raw) if raw else None

        with self._fallback_lock:
            try:
                record = self._cache.get(key)
                if record:
                    self._cache.delete(key)
                    return record
            except Exception:
                pass
            record = self._memory_store.get(key)
            if record:
                self._memory_store.pop(key, None)
            return record

    def _from_record(self, record: dict) -> CallbackStateRecord:
        return CallbackStateRecord(
            state=record["state"],
            user_id=record["user_id"],
            broker_details_id=record["broker_details_id"],
            client_code=record["client_code"],
            frontend_redirect_url=record.get("frontend_redirect_url"),
            created_at=datetime.fromisoformat(record["created_at"]),
            expires_at=datetime.fromisoformat(record["expires_at"]),
        )
