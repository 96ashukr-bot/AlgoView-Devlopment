from __future__ import annotations

import logging
from datetime import datetime
from typing import Any, Dict, Optional

from django.db import connection
from django.utils import timezone

from main.angelone.services.auth_service import AuthService
from main.angelone.utils.crypto import decrypt_value
from main.angelone.managers.session_manager import SessionManager
from main.models import ClientBrokerdetails, User, UserActivityLog

logger = logging.getLogger(__name__)


class LoginActivityService:
    def _clientbroker_columns(self) -> set[str]:
        with connection.cursor() as cursor:
            description = connection.introspection.get_table_description(cursor, ClientBrokerdetails._meta.db_table)
        return {column.name for column in description}

    def _current_request_login_time(self, request=None) -> Optional[str]:
        if not request:
            return None

        token = getattr(request, "auth", None)
        if not token:
            return None

        issued_at = None
        try:
            if hasattr(token, "get"):
                issued_at = token.get("iat")
            elif isinstance(token, dict):
                issued_at = token.get("iat")
        except Exception:
            issued_at = None

        if not issued_at:
            return None

        try:
            issued_at_dt = datetime.fromtimestamp(int(issued_at), tz=timezone.utc)
        except (TypeError, ValueError, OSError):
            return None

        return issued_at_dt.isoformat()

    def _latest_panel_activity(self, user: User, request=None) -> Dict[str, Optional[str]]:
        current_session = (
            UserActivityLog.objects.filter(user=user, last_login_time__isnull=False)
            .filter(last_logout_time__isnull=True)
            .order_by("-last_login_time")
            .first()
        )
        latest_session = (
            UserActivityLog.objects.filter(user=user, last_login_time__isnull=False)
            .order_by("-last_login_time")
            .first()
        )
        latest_completed = (
            UserActivityLog.objects.filter(
                user=user,
                last_login_time__isnull=False,
                last_logout_time__isnull=False,
            )
            .order_by("-last_logout_time", "-last_login_time")
            .first()
        )

        request_login_time = self._current_request_login_time(request)
        current_panel_login_time = request_login_time or (
            current_session.last_login_time.isoformat() if current_session and current_session.last_login_time else None
        )

        return {
            "current_panel_login_time": current_panel_login_time,
            "previous_panel_login_time": latest_completed.last_login_time.isoformat() if latest_completed and latest_completed.last_login_time else None,
            "panel_login_time": current_panel_login_time or (
                latest_session.last_login_time.isoformat() if latest_session and latest_session.last_login_time else None
            ),
            "panel_logout_time": latest_completed.last_logout_time.isoformat() if latest_completed and latest_completed.last_logout_time else None,
        }

    def _has_secret_value(self, value: Any) -> bool:
        return bool(decrypt_value(value))

    def _has_recoverable_auth(self, broker_payload: Dict[str, Any]) -> bool:
        has_refresh_token = self._has_secret_value(broker_payload.get("encrypted_refresh_token"))
        has_credentials = bool(
            self._has_secret_value(broker_payload.get("encrypted_broker_password"))
            and self._has_secret_value(broker_payload.get("encrypted_broker_totp_secret"))
        )
        return has_refresh_token or has_credentials

    def _token_status(self, broker_payload: Dict[str, Any]) -> Dict[str, Any]:
        access_token = decrypt_value(broker_payload.get("encrypted_access_token"))
        refresh_token = decrypt_value(broker_payload.get("encrypted_refresh_token"))
        feed_token = decrypt_value(broker_payload.get("encrypted_feed_token"))
        expiry = broker_payload.get("access_token_expiry")
        now = timezone.now()

        if not access_token:
            return {
                "status": "unavailable",
                "expires_at": None,
                "is_active": False,
                "is_expired": False,
                "has_refresh_token": bool(refresh_token),
                "has_feed_token": bool(feed_token),
            }

        is_expired = False
        if expiry:
            is_expired = expiry <= now
        elif broker_payload.get("isTokenExpired") is not None:
            is_expired = bool(broker_payload.get("isTokenExpired"))

        return {
            "status": "expired" if is_expired else "active",
            "expires_at": expiry.isoformat() if expiry else None,
            "is_active": not is_expired,
            "is_expired": is_expired,
            "has_refresh_token": bool(refresh_token),
            "has_feed_token": bool(feed_token),
        }

    def _session_status(self, broker_payload: Dict[str, Any], token_status: Dict[str, Any]) -> Dict[str, Any]:
        client_code = (broker_payload.get("broker_Demate_User_Name") or broker_payload.get("broker_API_UID") or "").strip() or None
        api_key = (broker_payload.get("broker_API_KEY") or "").strip() or None
        if not client_code or not api_key:
            return {
                "status": "unavailable",
                "is_active": False,
                "last_activity_at": None,
                "validated_at": None,
                "source": "missing_configuration",
            }

        live_lookup_failed = False
        try:
            session = SessionManager.get_instance().get_session(client_code, api_key)
        except Exception:
            live_lookup_failed = True
            logger.warning(
                "Unable to resolve broker session status for login activity summary",
                extra={
                    "client_code_present": bool(client_code),
                    "api_key_present": bool(api_key),
                },
                exc_info=True,
            )
            return {
                "status": "active" if token_status.get("status") in {"active", "expired"} and self._has_recoverable_auth(broker_payload) else "unavailable",
                "is_active": bool(token_status.get("status") in {"active", "expired"} and self._has_recoverable_auth(broker_payload)),
                "last_activity_at": broker_payload.get("tokenCreatedAt").isoformat() if broker_payload.get("tokenCreatedAt") else None,
                "validated_at": None,
                "source": "persisted_recovery" if token_status.get("status") in {"active", "expired"} and self._has_recoverable_auth(broker_payload) else "session_store_unavailable",
            }

        is_active = bool(session and session.is_valid())
        if is_active:
            return {
                "status": "active",
                "is_active": True,
                "last_activity_at": session.last_activity.isoformat() if session and session.last_activity else None,
                "validated_at": session.validated_at.isoformat() if session and session.validated_at else None,
                "source": "redis",
            }

        recoverable_auth = self._has_recoverable_auth(broker_payload)
        if token_status.get("status") == "active":
            return {
                "status": "active",
                "is_active": True,
                "last_activity_at": broker_payload.get("tokenCreatedAt").isoformat() if broker_payload.get("tokenCreatedAt") else None,
                "validated_at": None,
                "source": "persisted_token",
            }

        if token_status.get("status") == "expired" and recoverable_auth:
            return {
                "status": "active",
                "is_active": True,
                "last_activity_at": broker_payload.get("tokenCreatedAt").isoformat() if broker_payload.get("tokenCreatedAt") else None,
                "validated_at": None,
                "source": "recoverable_auth",
            }

        return {
            "status": "inactive" if not live_lookup_failed else "unavailable",
            "is_active": False,
            "last_activity_at": session.last_activity.isoformat() if session and session.last_activity else None,
            "validated_at": session.validated_at.isoformat() if session and session.validated_at else None,
            "source": "no_valid_session" if not live_lookup_failed else "session_store_unavailable",
        }

    def _broker_activity(self, user: User) -> Dict[str, Any]:
        available_columns = self._clientbroker_columns()
        selected_fields = [
            "broker_name__broker_name",
            "broker_API_KEY",
            "broker_API_UID",
            "broker_Demate_User_Name",
            "encrypted_broker_password",
            "encrypted_broker_totp_secret",
            "encrypted_access_token",
            "encrypted_refresh_token",
            "encrypted_feed_token",
            "access_token_expiry",
            "isTokenExpired",
            "tokenCreatedAt",
        ]
        if "broker_last_logout_at" in available_columns:
            selected_fields.append("broker_last_logout_at")

        broker_details = ClientBrokerdetails.objects.filter(client=user).select_related("broker_name").first()
        broker_payload = (
            ClientBrokerdetails.objects.filter(client=user)
            .values(*selected_fields)
            .first()
        )

        if not broker_payload or not broker_details:
            return {
                "is_configured": False,
                "broker_name": None,
                "client_code": None,
                "session": {
                    "status": "unavailable",
                    "is_active": False,
                    "last_activity_at": None,
                    "validated_at": None,
                },
                "token": {
                    "status": "unavailable",
                    "is_active": False,
                    "is_expired": False,
                    "expires_at": None,
                },
                "last_login_at": None,
                "last_logout_at": None,
            }

        token_status = self._token_status(broker_payload)
        session_status = self._session_status(broker_payload, token_status)

        client_code = (broker_payload.get("broker_Demate_User_Name") or broker_payload.get("broker_API_UID") or "").strip() or None
        api_key = (broker_payload.get("broker_API_KEY") or "").strip() or None

        if client_code and api_key and (not session_status.get("is_active")) and self._has_recoverable_auth(broker_payload):
            try:
                ensure = AuthService().ensure_valid_session(
                    client_id=client_code,
                    api_key=api_key,
                    broker_details=broker_details,
                    verify_remote=True,
                )
                if ensure.get("status") == "success":
                    refreshed_payload = {
                        **broker_payload,
                        "encrypted_access_token": broker_details.encrypted_access_token,
                        "encrypted_refresh_token": broker_details.encrypted_refresh_token,
                        "encrypted_feed_token": broker_details.encrypted_feed_token,
                        "access_token_expiry": broker_details.access_token_expiry,
                        "isTokenExpired": broker_details.isTokenExpired,
                        "tokenCreatedAt": broker_details.tokenCreatedAt,
                        "broker_last_logout_at": getattr(broker_details, "broker_last_logout_at", None),
                    }
                    token_status = self._token_status(refreshed_payload)
                    session = ensure.get("session")
                    session_status = {
                        "status": "active",
                        "is_active": True,
                        "last_activity_at": session.last_activity.isoformat() if session and session.last_activity else (
                            broker_details.tokenCreatedAt.isoformat() if broker_details.tokenCreatedAt else None
                        ),
                        "validated_at": session.validated_at.isoformat() if session and session.validated_at else None,
                        "source": ensure.get("source") or "ensure_valid_session",
                    }
                    broker_payload = refreshed_payload
            except Exception:
                logger.warning("Failed to resolve broker status via ensure_valid_session", exc_info=True)

        return {
            "is_configured": True,
            "broker_name": broker_payload.get("broker_name__broker_name"),
            "client_code": (broker_payload.get("broker_Demate_User_Name") or broker_payload.get("broker_API_UID") or "").strip() or None,
            "session": session_status,
            "token": token_status,
            "last_login_at": broker_payload.get("tokenCreatedAt").isoformat() if broker_payload.get("tokenCreatedAt") else None,
            "last_logout_at": broker_payload.get("broker_last_logout_at").isoformat() if broker_payload.get("broker_last_logout_at") else None,
        }

    def build_summary(self, user: User, request=None) -> Dict[str, Any]:
        panel = self._latest_panel_activity(user, request=request)
        broker = self._broker_activity(user)
        return {
            "status": "success",
            "data": {
                "panel": panel,
                "broker": broker,
            },
        }
