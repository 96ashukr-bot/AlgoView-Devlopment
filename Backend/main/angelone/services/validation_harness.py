from __future__ import annotations

import json
import time
import traceback
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextlib import contextmanager, nullcontext
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
from unittest import mock

from django.core.cache import caches
from django.conf import settings
from django.utils import timezone

from main.models import ClientBrokerdetails

from ..managers.session_manager import SessionManager
from ..utils.logging_utils import TradingLogger
from .auth_service import AuthService

logger = TradingLogger("validation_harness")


@dataclass
class ValidationResult:
    name: str
    passed: bool
    severity: str = "critical"
    duration_ms: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


class AngelOneValidationHarness:
    def __init__(self):
        self.auth_service = AuthService()
        self.session_manager = SessionManager.get_instance()

    def _run_named(self, name: str, func) -> Dict[str, Any]:
        start = time.perf_counter()
        try:
            outcome = func()
            duration_ms = round((time.perf_counter() - start) * 1000, 2)

            if isinstance(outcome, ValidationResult):
                outcome.name = name
                result_payload = asdict(outcome)
                success = outcome.passed
                error = outcome.error
            else:
                result_payload = outcome
                success = True
                error = None

            logger.info(
                "Validation step completed",
                step=name,
                success=success,
                duration_ms=duration_ms,
            )
            return {
                "name": name,
                "success": success,
                "result": result_payload,
                "error": error,
                "traceback": None,
            }
        except Exception as exc:
            duration_ms = round((time.perf_counter() - start) * 1000, 2)
            formatted_traceback = traceback.format_exc()
            logger.exception(
                "Validation step failed",
                step=name,
                error=str(exc),
                duration_ms=duration_ms,
            )
            return {
                "name": name,
                "success": False,
                "result": None,
                "error": str(exc),
                "traceback": formatted_traceback,
            }

    def resolve_broker_details(
        self,
        *,
        broker_details_id: Optional[int] = None,
        user_email: Optional[str] = None,
        client_code: Optional[str] = None,
    ) -> ClientBrokerdetails:
        queryset = ClientBrokerdetails.objects.select_related("client", "broker_name").filter(
            broker_name__broker_name__iexact="angel one"
        )
        if broker_details_id:
            broker_details = queryset.filter(id=broker_details_id).first()
        elif user_email:
            broker_details = queryset.filter(client__email__iexact=user_email).first()
        elif client_code:
            broker_details = queryset.filter(
                broker_Demate_User_Name=client_code
            ).first() or queryset.filter(broker_API_UID=client_code).first()
        else:
            raise ValueError("One of broker_details_id, user_email, or client_code is required")

        if not broker_details:
            raise ValueError("Angel One broker details not found for the supplied selector")
        return broker_details

    def check_prerequisites(self) -> Dict[str, Any]:
        checks: List[Dict[str, Any]] = []

        checks.append(self._enrich_dependency_check(self._run_named("redis_session_store", self._check_session_redis)))
        checks.append(
            self._enrich_dependency_check(
                self._run_named("redis_circuit_breaker_cache", self._check_circuit_breaker_cache)
            )
        )

        failures = [item for item in checks if not item["success"]]
        return {
            "status": "success" if not failures else "error",
            "context": {
                "redis_url": self._safe_redis_target(),
            },
            "checks": checks,
            "failure_count": len(failures),
        }

    def _enrich_dependency_check(self, check: Dict[str, Any]) -> Dict[str, Any]:
        if check["name"] in {"redis_session_store", "redis_circuit_breaker_cache"}:
            check["target"] = self._safe_redis_target()
            if check["success"]:
                result = check.get("result")
                if isinstance(result, dict):
                    result["target"] = self._safe_redis_target()
            else:
                check["hints"] = self._redis_connection_hints()
        return check

    def _safe_redis_target(self) -> str:
        parsed = urlparse(getattr(settings, "REDIS_URL", "redis://localhost:6379/1"))
        scheme = parsed.scheme or "redis"
        host = parsed.hostname or "localhost"
        port = parsed.port or 6379
        path = parsed.path or "/1"
        return f"{scheme}://{host}:{port}{path}"

    def _redis_connection_hints(self) -> List[str]:
        return [
            f"Configured Redis target: {self._safe_redis_target()}",
            "Make sure a Redis server is listening on the configured host and port.",
            f"Verify connectivity with: redis-cli -u {self._safe_redis_target()} ping",
            "If you use local Redis on macOS with Homebrew, start it with: brew services start redis",
            "If Redis runs elsewhere, set REDIS_URL to the correct redis://<host>:<port>/<db> value before rerunning validation.",
        ]

    def run_plan(
        self,
        broker_details: ClientBrokerdetails,
        *,
        include_logout: bool = True,
        run_concurrency: bool = True,
        concurrency: int = 5,
        iterations: int = 10,
        inject: Optional[str] = None,
    ) -> Dict[str, Any]:
        results: List[Dict[str, Any]] = []
        results.append(self._run_named("login_flow", lambda: self.test_login_flow(broker_details, force_new=True)))
        results.append(self._run_named("session_reuse", lambda: self.test_session_reuse(broker_details)))
        results.append(self._run_named("token_refresh", lambda: self.test_refresh_flow(broker_details)))
        results.append(self._run_named("feed_token", lambda: self.test_feed_token(broker_details)))
        if run_concurrency:
            results.append(
                self._run_named(
                    "concurrent_session_validation",
                    lambda: self.test_concurrent_session_validation(
                        broker_details,
                        concurrency=concurrency,
                        iterations=iterations,
                    ),
                )
            )
        if inject:
            results.append(self._run_named(f"failure_injection:{inject}", lambda: self.test_failure_injection(broker_details, inject)))
        if include_logout:
            results.append(self._run_named("logout_flow", lambda: self.test_logout_flow(broker_details)))

        failures = [result for result in results if not result["success"]]
        return {
            "status": "success" if not failures else "error",
            "executed_at": timezone.now().isoformat(),
            "client_code": broker_details.get_canonical_client_code(),
            "results": results,
            "failure_count": len(failures),
            "passed_count": len(results) - len(failures),
        }

    def _check_session_redis(self) -> Dict[str, Any]:
        self.session_manager._redis.ping()
        return {"message": "Session Redis is reachable"}

    def _check_circuit_breaker_cache(self) -> Dict[str, Any]:
        cache = caches["circuit_breaker"]
        key = "angelone:validation:preflight"
        cache.set(key, "ok", timeout=5)
        value = cache.get(key)
        cache.delete(key)
        if value != "ok":
            raise RuntimeError("Circuit breaker cache read/write verification failed")
        return {"message": "Circuit breaker cache is reachable"}

    def test_login_flow(self, broker_details: ClientBrokerdetails, force_new: bool = True) -> ValidationResult:
        credentials = self.auth_service.resolve_login_credentials(
            client_id=broker_details.get_canonical_client_code(),
            password=None,
            totp_secret=None,
            api_key=broker_details.broker_API_KEY,
            broker_details=broker_details,
        )
        client_code = credentials.get("client_id")
        api_key = credentials.get("api_key")
        start = time.perf_counter()
        attempted_fresh_login = all(
            [
                client_code,
                api_key,
                credentials.get("password"),
                credentials.get("totp_secret"),
            ]
        )

        if attempted_fresh_login:
            result = self.auth_service.login(
                client_id=client_code,
                password=credentials.get("password"),
                totp_secret=credentials.get("totp_secret"),
                api_key=api_key,
                broker_details=broker_details,
                force_new=force_new,
            )
            session = self.auth_service.get_session(client_code, api_key)
            result_message = result.get("message")
            login_succeeded = result.get("status") == "success"
            source = "fresh_login"
        elif client_code and api_key:
            result = self.auth_service.ensure_valid_session(
                client_id=client_code,
                api_key=api_key,
                broker_details=broker_details,
                verify_remote=True,
            )
            session = result.get("session") or self.auth_service.get_session(client_code, api_key)
            result_message = result.get("message") or "Reused existing validated session"
            login_succeeded = result.get("status") == "success"
            source = result.get("source") or "validated_session"
        else:
            result = {"status": "error", "message": "Missing required credentials"}
            session = None
            result_message = result["message"]
            login_succeeded = False
            source = "missing_identifiers"

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        tokens_available = bool(session and session.access_token and session.refresh_token)
        return ValidationResult(
            name="login_flow",
            passed=login_succeeded and tokens_available,
            duration_ms=duration_ms,
            details={
                "message": result_message,
                "validation_source": source,
                "attempted_fresh_login": attempted_fresh_login,
                "has_client_code": bool(client_code),
                "has_api_key": bool(api_key),
                "has_password": bool(credentials.get("password")),
                "has_totp": bool(credentials.get("totp_secret")),
                "has_access_token": bool(session and session.access_token),
                "has_refresh_token": bool(session and session.refresh_token),
                "has_feed_token": bool(session and session.feed_token),
                "session_status": session.status.value if session else None,
            },
            error=None if login_succeeded else result_message,
        )

    def test_session_reuse(self, broker_details: ClientBrokerdetails) -> ValidationResult:
        client_code = broker_details.get_canonical_client_code()
        api_key = broker_details.broker_API_KEY
        start = time.perf_counter()
        first = self.auth_service.ensure_valid_session(client_code, api_key, broker_details=broker_details, verify_remote=True)
        second = self.auth_service.ensure_valid_session(client_code, api_key, broker_details=broker_details, verify_remote=False)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        session_one = first.get("session")
        session_two = second.get("session")
        same_key = bool(session_one and session_two and session_one.session_key == session_two.session_key)
        return ValidationResult(
            name="session_reuse",
            passed=first.get("status") == "success" and second.get("status") == "success" and same_key,
            duration_ms=duration_ms,
            severity="high",
            details={
                "first_source": first.get("source"),
                "second_source": second.get("source"),
                "same_session_key": same_key,
            },
            error=None if same_key else "Session reuse failed or new session was created unexpectedly",
        )

    def test_refresh_flow(self, broker_details: ClientBrokerdetails) -> ValidationResult:
        client_code = broker_details.get_canonical_client_code()
        api_key = broker_details.broker_API_KEY
        start = time.perf_counter()
        ensure = self.auth_service.ensure_valid_session(client_code, api_key, broker_details=broker_details, verify_remote=True)
        before = self.auth_service.get_session(client_code, api_key)
        result = self.auth_service.refresh_session(client_code, api_key)
        after = self.auth_service.get_session(client_code, api_key)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        rotated_or_valid = bool(after and after.access_token and after.refresh_token and after.feed_token)
        return ValidationResult(
            name="token_refresh",
            passed=ensure.get("status") == "success" and result.get("status") == "success" and rotated_or_valid,
            duration_ms=duration_ms,
            details={
                "refresh_message": result.get("message"),
                "before_session_expiry": before.session_expiry.isoformat() if before and before.session_expiry else None,
                "after_session_expiry": after.session_expiry.isoformat() if after and after.session_expiry else None,
                "has_feed_token_after_refresh": bool(after and after.feed_token),
            },
            error=None if result.get("status") == "success" else result.get("message"),
        )

    def test_feed_token(self, broker_details: ClientBrokerdetails) -> ValidationResult:
        client_code = broker_details.get_canonical_client_code()
        api_key = broker_details.broker_API_KEY
        start = time.perf_counter()
        ensure = self.auth_service.ensure_valid_session(client_code, api_key, broker_details=broker_details, verify_remote=True)
        session = ensure.get("session")
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        feed_token = session.feed_token if session else None
        smart_feed_token = None
        if session and session.smart_connect:
            try:
                smart_feed_token = session.smart_connect.getfeedToken()
            except Exception as exc:
                return ValidationResult(
                    name="feed_token",
                    passed=False,
                    duration_ms=duration_ms,
                    error=str(exc),
                    details={"message": "SmartConnect getfeedToken() failed"},
                )

        return ValidationResult(
            name="feed_token",
            passed=ensure.get("status") == "success" and bool(feed_token) and bool(smart_feed_token or feed_token),
            duration_ms=duration_ms,
            details={
                "has_session_feed_token": bool(feed_token),
                "has_sdk_feed_token": bool(smart_feed_token),
            },
            error=None if feed_token else "Feed token missing after validated session build",
        )

    def test_logout_flow(self, broker_details: ClientBrokerdetails) -> ValidationResult:
        client_code = broker_details.get_canonical_client_code()
        api_key = broker_details.broker_API_KEY
        start = time.perf_counter()
        ensure = self.auth_service.ensure_valid_session(client_code, api_key, broker_details=broker_details, verify_remote=True)
        result = self.auth_service.logout(client_code, api_key)
        session = self.auth_service.get_session(client_code, api_key)
        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        return ValidationResult(
            name="logout_flow",
            passed=ensure.get("status") == "success" and result.get("status") == "success" and session is None,
            duration_ms=duration_ms,
            details={"logout_message": result.get("message"), "session_removed": session is None},
            error=None if session is None else "Redis/shared session still present after logout",
        )

    def test_concurrent_session_validation(
        self,
        broker_details: ClientBrokerdetails,
        *,
        concurrency: int = 5,
        iterations: int = 10,
    ) -> ValidationResult:
        client_code = broker_details.get_canonical_client_code()
        api_key = broker_details.broker_API_KEY
        start = time.perf_counter()

        def worker() -> Dict[str, Any]:
            local_success = 0
            local_failures: List[str] = []
            for _ in range(iterations):
                result = self.auth_service.ensure_valid_session(
                    client_id=client_code,
                    api_key=api_key,
                    broker_details=broker_details,
                    verify_remote=True,
                )
                if result.get("status") == "success":
                    local_success += 1
                else:
                    local_failures.append(result.get("message", "unknown error"))
            return {"success": local_success, "failures": local_failures}

        aggregate_success = 0
        failures: List[str] = []
        with ThreadPoolExecutor(max_workers=concurrency) as pool:
            futures = [pool.submit(worker) for _ in range(concurrency)]
            for future in as_completed(futures):
                outcome = future.result()
                aggregate_success += outcome["success"]
                failures.extend(outcome["failures"])

        duration_ms = round((time.perf_counter() - start) * 1000, 2)
        return ValidationResult(
            name="concurrent_session_validation",
            passed=not failures and aggregate_success == concurrency * iterations,
            severity="high",
            duration_ms=duration_ms,
            details={
                "concurrency": concurrency,
                "iterations_per_worker": iterations,
                "successful_validations": aggregate_success,
                "expected_validations": concurrency * iterations,
            },
            error="; ".join(failures[:3]) if failures else None,
        )

    def test_failure_injection(self, broker_details: ClientBrokerdetails, mode: str) -> ValidationResult:
        client_code = broker_details.get_canonical_client_code()
        api_key = broker_details.broker_API_KEY
        start = time.perf_counter()
        ctx = self._failure_context(mode)
        with ctx:
            if mode == "invalid_credentials":
                result = self.auth_service.login(
                    client_id=client_code,
                    password="invalid-password",
                    totp_secret=broker_details.get_broker_totp_secret() or "",
                    api_key=api_key,
                    broker_details=broker_details,
                    force_new=True,
                )
            else:
                result = self.auth_service.ensure_valid_session(
                    client_id=client_code,
                    api_key=api_key,
                    broker_details=broker_details,
                    verify_remote=True,
                )
        duration_ms = round((time.perf_counter() - start) * 1000, 2)

        expect_failure = mode in {"redis_down", "broker_down", "network_timeout", "invalid_credentials"}
        passed = expect_failure and result.get("status") == "error"
        return ValidationResult(
            name=f"failure_injection:{mode}",
            passed=passed,
            severity="high",
            duration_ms=duration_ms,
            details={"message": result.get("message"), "mode": mode},
            error=None if passed else f"Expected failure for mode {mode}, got {json.dumps(result, default=str)}",
        )

    @contextmanager
    def _failure_context(self, mode: str):
        if mode == "redis_down":
            side_effect = ConnectionError("Injected Redis outage")
            with mock.patch.object(self.session_manager, "_redis", autospec=False) as fake_redis:
                fake_redis.lock.side_effect = side_effect
                fake_redis.get.side_effect = side_effect
                fake_redis.set.side_effect = side_effect
                fake_redis.delete.side_effect = side_effect
                yield
            return

        if mode == "broker_down":
            with mock.patch("main.angelone.managers.session_manager.SmartConnect.generateSession", side_effect=ConnectionError("Injected broker outage")), \
                 mock.patch("main.angelone.managers.session_manager.SmartConnect.generateToken", side_effect=ConnectionError("Injected broker outage")), \
                 mock.patch("main.angelone.managers.session_manager.SmartConnect.getProfile", side_effect=ConnectionError("Injected broker outage")):
                yield
            return

        if mode == "network_timeout":
            with mock.patch("main.angelone.managers.session_manager.SmartConnect.generateSession", side_effect=TimeoutError("Injected network timeout")), \
                 mock.patch("main.angelone.managers.session_manager.SmartConnect.generateToken", side_effect=TimeoutError("Injected network timeout")), \
                 mock.patch("main.angelone.managers.session_manager.SmartConnect.getProfile", side_effect=TimeoutError("Injected network timeout")):
                yield
            return

        if mode == "invalid_credentials":
            yield
            return

        with nullcontext():
            yield
