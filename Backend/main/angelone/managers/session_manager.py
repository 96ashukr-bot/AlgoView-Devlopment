"""
Redis-backed multi-worker-safe session manager for Angel One SmartAPI.
"""

from __future__ import annotations

import hashlib
import json
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any

import pyotp
import redis
from SmartApi import SmartConnect
from django.conf import settings
from django.utils import timezone

from ..constants import REFRESH_TOKEN_EXPIRY_DAYS, SESSION_EXPIRY_HOURS
from ..services.circuit_breaker import BrokerAuthCircuitBreaker
from ..utils.crypto import decrypt_value, encrypt_value
from ..utils.logging_utils import TradingLogger

logger = TradingLogger("session_manager")


class _LocalSessionLock:
    def acquire(self, blocking=True):
        return True

    def release(self):
        return None


class _UnavailableRedisClient:
    def _raise(self, *args, **kwargs):
        raise redis.ConnectionError("Redis is not configured")

    get = _raise
    set = _raise
    delete = _raise
    ping = _raise

    def lock(self, *args, **kwargs):
        return _LocalSessionLock()


class SessionStatus(Enum):
    ACTIVE = "active"
    EXPIRED = "expired"
    REFRESHING = "refreshing"
    INVALID = "invalid"
    NOT_INITIALIZED = "not_initialized"


@dataclass
class ClientSession:
    client_id: str
    api_key: str
    session_key: str
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    feed_token: Optional[str] = None
    session_expiry: Optional[datetime] = None
    refresh_token_expiry: Optional[datetime] = None
    validated_at: Optional[datetime] = None
    remote_validation_due_at: Optional[datetime] = None
    status: SessionStatus = SessionStatus.NOT_INITIALIZED
    last_activity: Optional[datetime] = None
    login_time: Optional[datetime] = None
    broker_user_id: Optional[str] = None
    source: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)
    _lock: threading.RLock = field(default_factory=threading.RLock)
    smart_connect: Optional[SmartConnect] = None

    def is_valid(self) -> bool:
        with self._lock:
            if self.status != SessionStatus.ACTIVE or not self.access_token:
                return False
            if self.session_expiry and timezone.now() > self.session_expiry:
                self.status = SessionStatus.EXPIRED
                return False
            return True

    def can_refresh(self) -> bool:
        with self._lock:
            if not self.refresh_token:
                return False
            if self.refresh_token_expiry and timezone.now() > self.refresh_token_expiry:
                return False
            return True

    def requires_remote_validation(self) -> bool:
        if not self.remote_validation_due_at:
            return True
        return timezone.now() >= self.remote_validation_due_at

    def update_activity(self):
        with self._lock:
            self.last_activity = timezone.now()

    def attach_smart_connect(self) -> SmartConnect:
        with self._lock:
            obj = SmartConnect(api_key=self.api_key)
            if self.access_token:
                obj.setAccessToken(self.access_token)
            if self.refresh_token:
                obj.setRefreshToken(self.refresh_token)
            if self.feed_token:
                obj.setFeedToken(self.feed_token)
            self.smart_connect = obj
            return obj

    def to_dict(self) -> Dict[str, Any]:
        return {
            "client_id": self.client_id,
            "status": self.status.value,
            "session_expiry": self.session_expiry.isoformat() if self.session_expiry else None,
            "refresh_token_expiry": self.refresh_token_expiry.isoformat() if self.refresh_token_expiry else None,
            "validated_at": self.validated_at.isoformat() if self.validated_at else None,
            "remote_validation_due_at": self.remote_validation_due_at.isoformat() if self.remote_validation_due_at else None,
            "last_activity": self.last_activity.isoformat() if self.last_activity else None,
            "login_time": self.login_time.isoformat() if self.login_time else None,
            "broker_user_id": self.broker_user_id,
            "source": self.source,
            "has_feed_token": self.feed_token is not None,
        }


class SessionManager:
    _instance: Optional["SessionManager"] = None
    _instance_lock = threading.Lock()
    _fallback_store: Dict[str, Dict[str, Any]] = {}
    _fallback_store_lock = threading.RLock()

    def __init__(self):
        redis_url = (getattr(settings, "REDIS_URL", "") or "").strip()
        try:
            self._redis = redis.Redis.from_url(redis_url, decode_responses=True) if redis_url else _UnavailableRedisClient()
        except Exception:
            self._redis = _UnavailableRedisClient()
        self._breaker = BrokerAuthCircuitBreaker("angelone")
        self._remote_validation_ttl = settings.ANGELONE_REMOTE_VALIDATION_TTL_SECONDS
        self._session_ttl = settings.ANGELONE_SESSION_TTL_SECONDS
        self._lock_timeout = settings.ANGELONE_LOGIN_LOCK_SECONDS
        self._lock_wait = settings.ANGELONE_LOGIN_LOCK_WAIT_SECONDS
        self._prefix = settings.ANGELONE_SESSION_CACHE_PREFIX
        self._lock_prefix = settings.ANGELONE_LOCK_CACHE_PREFIX

    @classmethod
    def get_instance(cls) -> "SessionManager":
        if cls._instance is None:
            with cls._instance_lock:
                if cls._instance is None:
                    cls._instance = SessionManager()
        return cls._instance

    def _cache_key(self, session_key: str) -> str:
        return f"{self._prefix}:{session_key}"

    def _lock_key(self, session_key: str) -> str:
        return f"{self._lock_prefix}:{session_key}"

    def _get_session_key(self, client_id: str, api_key: str) -> str:
        return hashlib.sha256(f"{client_id}:{api_key}".encode("utf-8")).hexdigest()

    def _normalize_access_token(self, token: Optional[str]) -> Optional[str]:
        if not token:
            return None
        if token.startswith("Bearer "):
            return token.split(" ", 1)[1]
        return token

    def _parse_datetime(self, value: Optional[str]) -> Optional[datetime]:
        if not value:
            return None
        return datetime.fromisoformat(value)

    def _session_from_payload(self, payload: Dict[str, Any]) -> ClientSession:
        session = ClientSession(
            client_id=payload["client_id"],
            api_key=decrypt_value(payload["api_key"]) or "",
            session_key=payload["session_key"],
            access_token=decrypt_value(payload.get("access_token")),
            refresh_token=decrypt_value(payload.get("refresh_token")),
            feed_token=decrypt_value(payload.get("feed_token")),
            session_expiry=self._parse_datetime(payload.get("session_expiry")),
            refresh_token_expiry=self._parse_datetime(payload.get("refresh_token_expiry")),
            validated_at=self._parse_datetime(payload.get("validated_at")),
            remote_validation_due_at=self._parse_datetime(payload.get("remote_validation_due_at")),
            status=SessionStatus(payload.get("status", SessionStatus.NOT_INITIALIZED.value)),
            last_activity=self._parse_datetime(payload.get("last_activity")),
            login_time=self._parse_datetime(payload.get("login_time")),
            broker_user_id=payload.get("broker_user_id"),
            source=payload.get("source", "unknown"),
            metadata=payload.get("metadata", {}) or {},
        )
        session.attach_smart_connect()
        return session

    def _payload_from_session(self, session: ClientSession) -> Dict[str, Any]:
        return {
            "client_id": session.client_id,
            "api_key": encrypt_value(session.api_key),
            "session_key": session.session_key,
            "access_token": encrypt_value(session.access_token),
            "refresh_token": encrypt_value(session.refresh_token),
            "feed_token": encrypt_value(session.feed_token),
            "session_expiry": session.session_expiry.isoformat() if session.session_expiry else None,
            "refresh_token_expiry": session.refresh_token_expiry.isoformat() if session.refresh_token_expiry else None,
            "validated_at": session.validated_at.isoformat() if session.validated_at else None,
            "remote_validation_due_at": session.remote_validation_due_at.isoformat() if session.remote_validation_due_at else None,
            "status": session.status.value,
            "last_activity": session.last_activity.isoformat() if session.last_activity else None,
            "login_time": session.login_time.isoformat() if session.login_time else None,
            "broker_user_id": session.broker_user_id,
            "source": session.source,
            "metadata": session.metadata,
        }

    def _persist_session(self, session: ClientSession) -> None:
        ttl = self._session_ttl
        if session.refresh_token_expiry:
            remaining = int((session.refresh_token_expiry - timezone.now()).total_seconds())
            ttl = max(60, min(ttl, remaining)) if remaining > 0 else 60
        cache_key = self._cache_key(session.session_key)
        payload = json.dumps(self._payload_from_session(session))
        try:
            self._redis.set(cache_key, payload, ex=ttl)
        except Exception:
            with self._fallback_store_lock:
                self._fallback_store[cache_key] = {
                    "payload": payload,
                    "expires_at": timezone.now() + timedelta(seconds=ttl),
                }

    def _delete_session(self, session_key: str) -> None:
        cache_key = self._cache_key(session_key)
        try:
            self._redis.delete(cache_key)
        except Exception:
            with self._fallback_store_lock:
                self._fallback_store.pop(cache_key, None)

    def invalidate_local_session(self, client_id: str, api_key: str) -> None:
        self._delete_session(self._get_session_key(client_id, api_key))

    def _get_cached_session(self, session_key: str) -> Optional[ClientSession]:
        cache_key = self._cache_key(session_key)
        payload = None
        try:
            payload = self._redis.get(cache_key)
        except Exception:
            with self._fallback_store_lock:
                record = self._fallback_store.get(cache_key)
                if record:
                    if record["expires_at"] <= timezone.now():
                        self._fallback_store.pop(cache_key, None)
                    else:
                        payload = record["payload"]
        if not payload:
            return None
        try:
            return self._session_from_payload(json.loads(payload))
        except Exception as exc:
            logger.error("Failed to deserialize cached session", error=str(exc), session_key=session_key)
            self._delete_session(session_key)
            return None

    def _get_lock(self, session_key: str):
        try:
            return self._redis.lock(
                self._lock_key(session_key),
                timeout=self._lock_timeout,
                blocking_timeout=self._lock_wait,
            )
        except Exception:
            return _LocalSessionLock()

    def _build_session(
        self,
        client_id: str,
        api_key: str,
        access_token: Optional[str],
        refresh_token: Optional[str],
        feed_token: Optional[str],
        source: str,
        broker_user_id: Optional[str] = None,
        validated: bool = False,
        session_expiry: Optional[datetime] = None,
        refresh_token_expiry: Optional[datetime] = None,
    ) -> ClientSession:
        now = timezone.now()
        session = ClientSession(
            client_id=client_id,
            api_key=api_key,
            session_key=self._get_session_key(client_id, api_key),
            access_token=self._normalize_access_token(access_token),
            refresh_token=refresh_token,
            feed_token=feed_token,
            session_expiry=session_expiry or (now + timedelta(hours=SESSION_EXPIRY_HOURS)),
            refresh_token_expiry=refresh_token_expiry or (
                now + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS) if refresh_token else None
            ),
            validated_at=now if validated else None,
            remote_validation_due_at=(now + timedelta(seconds=self._remote_validation_ttl)) if validated else now,
            status=SessionStatus.ACTIVE if access_token else SessionStatus.NOT_INITIALIZED,
            last_activity=now,
            login_time=now,
            broker_user_id=broker_user_id,
            source=source,
        )
        session.attach_smart_connect()
        return session

    def _remote_validate(self, session: ClientSession) -> bool:
        if not session.refresh_token:
            return False
        obj = session.smart_connect or session.attach_smart_connect()
        profile = obj.getProfile(session.refresh_token)
        if not isinstance(profile, dict) or not profile.get("status"):
            return False
        now = timezone.now()
        session.validated_at = now
        session.remote_validation_due_at = now + timedelta(seconds=self._remote_validation_ttl)
        session.last_activity = now
        session.status = SessionStatus.ACTIVE
        data = profile.get("data", {}) or {}
        session.broker_user_id = data.get("clientcode") or session.broker_user_id or session.client_id
        return True

    def get_session(self, client_id: str, api_key: Optional[str] = None) -> Optional[ClientSession]:
        if not api_key:
            return None
        session_key = self._get_session_key(client_id, api_key)
        session = self._get_cached_session(session_key)
        if session:
            session.update_activity()
            self._persist_session(session)
        return session

    def create_session_from_tokens(
        self,
        client_id: str,
        api_key: str,
        access_token: str,
        refresh_token: Optional[str] = None,
        feed_token: Optional[str] = None,
        session_expiry: Optional[datetime] = None,
        refresh_token_expiry: Optional[datetime] = None,
        remote_verified: bool = False,
        persist: bool = True,
    ) -> Optional[ClientSession]:
        if not access_token:
            return None
        session = self._build_session(
            client_id=client_id,
            api_key=api_key,
            access_token=access_token,
            refresh_token=refresh_token,
            feed_token=feed_token,
            source="callback_tokens" if remote_verified else "persisted_tokens",
            validated=remote_verified,
            session_expiry=session_expiry,
            refresh_token_expiry=refresh_token_expiry,
        )
        if persist:
            self._persist_session(session)
        return session

    def login(
        self,
        client_id: str,
        password: str,
        totp_secret: str,
        api_key: str,
        force_new: bool = False,
    ) -> Dict[str, Any]:
        if self._breaker.is_open():
            return {"status": "error", "message": "Angel One auth circuit breaker is open. Retry shortly."}

        session_key = self._get_session_key(client_id, api_key)
        lock = self._get_lock(session_key)
        try:
            acquired = lock.acquire(blocking=True)
        except Exception:
            lock = _LocalSessionLock()
            acquired = lock.acquire(blocking=True)
        if not acquired:
            return {"status": "error", "message": "Could not acquire broker login lock"}

        try:
            return self._perform_login(client_id, password, totp_secret, api_key, force_new=force_new)
        except Exception as exc:
            self._breaker.record_failure()
            logger.exception("Login exception", client_id=client_id, error=str(exc))
            return {"status": "error", "message": str(exc)}
        finally:
            try:
                lock.release()
            except Exception:
                pass

    def refresh_session(self, client_id: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        if not api_key:
            return {"status": "error", "message": "API key is required"}
        if self._breaker.is_open():
            return {"status": "error", "message": "Angel One auth circuit breaker is open. Retry shortly."}

        session_key = self._get_session_key(client_id, api_key)
        lock = self._get_lock(session_key)
        try:
            acquired = lock.acquire(blocking=True)
        except Exception:
            lock = _LocalSessionLock()
            acquired = lock.acquire(blocking=True)
        if not acquired:
            return {"status": "error", "message": "Could not acquire broker refresh lock"}

        try:
            session = self._get_cached_session(session_key)
            return self._perform_refresh(session)
        except Exception as exc:
            self._breaker.record_failure()
            logger.error("Session refresh failed", client_id=client_id, error=str(exc))
            return {"status": "error", "message": str(exc)}
        finally:
            try:
                lock.release()
            except Exception:
                pass

    def validate_session(
        self,
        client_id: str,
        api_key: str,
        broker_details=None,
        verify_remote: bool = True,
    ) -> Dict[str, Any]:
        if self._breaker.is_open():
            return {"status": "error", "message": "Angel One auth circuit breaker is open. Retry shortly."}
        session_key = self._get_session_key(client_id, api_key)
        lock = self._get_lock(session_key)
        try:
            acquired = lock.acquire(blocking=True)
        except Exception:
            lock = _LocalSessionLock()
            acquired = lock.acquire(blocking=True)
        if not acquired:
            return {"status": "error", "message": "Could not acquire broker session lock"}

        try:
            session = self._get_cached_session(session_key)
            if session and session.is_valid():
                if not verify_remote or not session.requires_remote_validation() or self._remote_validate(session):
                    session.update_activity()
                    self._persist_session(session)
                    self._breaker.record_success()
                    return {"status": "success", "session": session, "source": "redis"}

            if broker_details:
                persisted_access_token = broker_details.get_access_token_secure()
                persisted_refresh_token = broker_details.get_refresh_token_secure()
                persisted_feed_token = broker_details.get_feed_token_secure()
                persisted_expiry = getattr(broker_details, "access_token_expiry", None)

                if persisted_access_token and persisted_refresh_token:
                    candidate = self._build_session(
                        client_id=client_id,
                        api_key=api_key,
                        access_token=persisted_access_token,
                        refresh_token=persisted_refresh_token,
                        feed_token=persisted_feed_token,
                        source="persisted_tokens",
                        session_expiry=persisted_expiry,
                        validated=False,
                    )
                    if self._remote_validate(candidate):
                        self._persist_session(candidate)
                        self._breaker.record_success()
                        return {"status": "success", "session": candidate, "source": "persisted_tokens"}

                if persisted_refresh_token:
                    refresh_seed = self._build_session(
                        client_id=client_id,
                        api_key=api_key,
                        access_token=persisted_access_token,
                        refresh_token=persisted_refresh_token,
                        feed_token=persisted_feed_token,
                        source="persisted_refresh",
                        session_expiry=persisted_expiry,
                    )
                    self._persist_session(refresh_seed)
                    refreshed = self._perform_refresh(refresh_seed)
                    if refreshed.get("status") == "success":
                        refreshed_session = self._get_cached_session(session_key)
                        return {"status": "success", "session": refreshed_session, "source": "refresh"}

                credentials = broker_details.get_angel_one_login_credentials()
                password = credentials.get("password")
                totp_secret = credentials.get("totp_secret")
                if password and totp_secret:
                    login_result = self._perform_login(
                        client_id=credentials.get("client_code") or client_id,
                        password=password,
                        totp_secret=totp_secret,
                        api_key=credentials.get("api_key") or api_key,
                        force_new=True,
                    )
                    if login_result.get("status") == "success":
                        login_session = self._get_cached_session(session_key)
                        return {"status": "success", "session": login_session, "source": "credential_login"}

            self._breaker.record_failure()
            return {"status": "error", "message": "No valid Angel One session is available. Please complete broker login again."}
        finally:
            try:
                lock.release()
            except Exception:
                pass

    def logout(self, client_id: str, api_key: Optional[str] = None) -> Dict[str, Any]:
        if not api_key:
            return {"status": "error", "message": "API key is required"}
        session_key = self._get_session_key(client_id, api_key)
        session = self._get_cached_session(session_key)
        if not session:
            return {"status": "success", "message": "Already logged out"}
        try:
            obj = session.smart_connect or session.attach_smart_connect()
            obj.terminateSession(client_id)
        except Exception as exc:
            logger.warning("Broker logout returned error", client_id=client_id, error=str(exc))
        self._delete_session(session_key)
        return {"status": "success", "message": "Logged out"}

    def get_smart_connect(self, client_id: str, api_key: Optional[str] = None) -> Optional[SmartConnect]:
        session = self.get_session(client_id, api_key)
        if session and session.is_valid():
            return session.smart_connect or session.attach_smart_connect()
        return None

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        result: Dict[str, Dict[str, Any]] = {}
        try:
            keys = list(self._redis.scan_iter(match=f"{self._prefix}:*"))
            for key in keys:
                payload = self._redis.get(key)
                if not payload:
                    continue
                try:
                    session = self._session_from_payload(json.loads(payload))
                    result[key] = session.to_dict()
                except Exception:
                    continue
        except Exception:
            with self._fallback_store_lock:
                for key, record in list(self._fallback_store.items()):
                    if not key.startswith(f"{self._prefix}:"):
                        continue
                    if record["expires_at"] <= timezone.now():
                        self._fallback_store.pop(key, None)
                        continue
                    try:
                        session = self._session_from_payload(json.loads(record["payload"]))
                        result[key] = session.to_dict()
                    except Exception:
                        continue
        return result

    def get_active_client_count(self) -> int:
        return sum(1 for session in self.get_all_sessions().values() if session.get("status") == SessionStatus.ACTIVE.value)

    def start_cleanup_thread(self, interval: int = 300):
        return None

    def stop_cleanup_thread(self):
        return None

    def _perform_login(
        self,
        client_id: str,
        password: str,
        totp_secret: str,
        api_key: str,
        force_new: bool = False,
    ) -> Dict[str, Any]:
        session_key = self._get_session_key(client_id, api_key)
        if not force_new:
            existing = self._get_cached_session(session_key)
            if existing and existing.is_valid() and not existing.requires_remote_validation():
                existing.update_activity()
                self._persist_session(existing)
                return {
                    "status": "success",
                    "message": "Using existing valid session",
                    "session": existing.to_dict(),
                    "access_token": existing.access_token,
                    "refresh_token": existing.refresh_token,
                    "feed_token": existing.feed_token,
                }

        totp = pyotp.TOTP(totp_secret).now()
        obj = SmartConnect(api_key=api_key)
        data = obj.generateSession(client_id, password, totp)
        if not isinstance(data, dict) or not data.get("status"):
            self._breaker.record_failure()
            return {"status": "error", "message": data.get("message", "Login failed") if isinstance(data, dict) else "Login failed"}

        profile_data = data.get("data", {}) or {}
        session = self._build_session(
            client_id=client_id,
            api_key=api_key,
            access_token=profile_data.get("jwtToken"),
            refresh_token=profile_data.get("refreshToken"),
            feed_token=profile_data.get("feedToken") or obj.getfeedToken(),
            source="credential_login",
            broker_user_id=profile_data.get("clientcode") or client_id,
            validated=True,
        )
        self._persist_session(session)
        self._breaker.record_success()
        return {
            "status": "success",
            "message": "Login successful",
            "session": session.to_dict(),
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "feed_token": session.feed_token,
        }

    def _perform_refresh(self, session: Optional[ClientSession]) -> Dict[str, Any]:
        if not session:
            return {"status": "error", "message": "Session not found"}
        if not session.can_refresh():
            return {"status": "error", "message": "Cannot refresh - token expired"}

        obj = session.smart_connect or session.attach_smart_connect()
        session.status = SessionStatus.REFRESHING
        data = obj.generateToken(session.refresh_token)
        if not isinstance(data, dict) or not data.get("status"):
            session.status = SessionStatus.INVALID
            self._persist_session(session)
            self._breaker.record_failure()
            return {"status": "error", "message": data.get("message", "Refresh failed") if isinstance(data, dict) else "Refresh failed"}

        response_data = data.get("data", {}) or {}
        now = timezone.now()
        session.access_token = self._normalize_access_token(response_data.get("jwtToken"))
        session.refresh_token = response_data.get("refreshToken", session.refresh_token)
        session.feed_token = response_data.get("feedToken") or session.feed_token or obj.getfeedToken()
        session.session_expiry = now + timedelta(hours=SESSION_EXPIRY_HOURS)
        session.refresh_token_expiry = now + timedelta(days=REFRESH_TOKEN_EXPIRY_DAYS)
        session.validated_at = now
        session.remote_validation_due_at = now + timedelta(seconds=self._remote_validation_ttl)
        session.status = SessionStatus.ACTIVE
        session.last_activity = now
        session.attach_smart_connect()
        self._persist_session(session)
        self._breaker.record_success()
        return {
            "status": "success",
            "message": "Session refreshed",
            "access_token": session.access_token,
            "refresh_token": session.refresh_token,
            "feed_token": session.feed_token,
        }
