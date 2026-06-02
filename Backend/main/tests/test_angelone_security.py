import os
import re
import subprocess
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock
from types import SimpleNamespace
from zoneinfo import ZoneInfo

from django.contrib.sessions.middleware import SessionMiddleware
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from main.angelone.managers.session_manager import SessionManager, SessionStatus
from main.angelone.managers.contract_manager import Contract
from main.angelone.constants import MARKET_CLOSE_HOUR, MARKET_CLOSE_MINUTE, TIMEZONE
from main.angelone.services.state_service import CallbackStateService
from main.angelone_views import angelone_callback
from main.execution_engine import ContractInfo, ExecutionEngine, ExecutionRequest
from main.angelone.services.order_service import OrderService, _optional_positive_float as angel_one_optional_price
from main.models import Broker, ClientBrokerdetails, OTP, Tradeorderhistory, User, UserActivityLog
from main.serializers import ClientBrokerDetailsSerializer, ClientBrokerDetailsUpdateSerializer, OTPVerifySerializer
from main.services.login_activity_service import LoginActivityService
from main.trade_history_service import save_trade_order_history
from main.views import AdminClientBrokerDetailsView, LoginActivitySummaryView
from django.utils import timezone


TEST_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "angelone-tests"},
    "circuit_breaker": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "angelone-circuit-tests"},
}


@override_settings(
    CACHES=TEST_CACHES,
    ANGELONE_STATE_CACHE_PREFIX="test:angelone:state",
    ANGELONE_CALLBACK_STATE_TTL_SECONDS=60,
)
class AngelOneCallbackSecurityTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="owner@example.com",
            firstName="Owner",
            lastName="User",
            phoneNumber="9999999991",
            password="Pass@1234",
        )
        self.other_user = User.objects.create_user(
            email="other@example.com",
            firstName="Other",
            lastName="User",
            phoneNumber="9999999992",
            password="Pass@1234",
        )
        self.broker = Broker.objects.create(broker_name="Angel One", is_active=True)
        self.broker_details = ClientBrokerdetails.objects.create(
            client=self.user,
            broker_name=self.broker,
            broker_API_KEY="api-key-123",
            broker_API_UID="A12345",
            broker_Demate_User_Name="A12345",
        )
        self.state_service = CallbackStateService()

    @mock.patch("main.angelone.services.auth_service.AuthService.register_existing_tokens")
    def test_callback_rejects_missing_state(self, mock_register):
        request = self.factory.get("/auth-callback/", {"access_token": "jwt", "refreshToken": "refresh"})
        request.user = self.user

        response = angelone_callback(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Missing mandatory callback state", response.content)
        mock_register.assert_not_called()

    @mock.patch("main.angelone.services.auth_service.AuthService.register_existing_tokens")
    def test_callback_rejects_replayed_state(self, mock_register):
        record = self.state_service.create(
            state="replay-state",
            user_id=self.user.id,
            broker_details_id=self.broker_details.id,
            client_code=self.broker_details.get_canonical_client_code(),
        )
        mock_register.return_value = {"status": "success"}

        request_one = self.factory.get(
            "/auth-callback/",
            {"state": record.state, "access_token": "jwt", "refreshToken": "refresh", "feedToken": "feed"},
        )
        request_one.user = self.user
        first = angelone_callback(request_one)

        request_two = self.factory.get(
            "/auth-callback/",
            {"state": record.state, "access_token": "jwt", "refreshToken": "refresh", "feedToken": "feed"},
        )
        request_two.user = self.user
        second = angelone_callback(request_two)

        self.assertEqual(first.status_code, 302)
        self.assertEqual(second.status_code, 400)
        self.assertIn(b"already used", second.content)

    @mock.patch("main.angelone.services.auth_service.AuthService.register_existing_tokens")
    def test_callback_rejects_authenticated_user_mismatch(self, mock_register):
        record = self.state_service.create(
            state="user-mismatch",
            user_id=self.user.id,
            broker_details_id=self.broker_details.id,
            client_code=self.broker_details.get_canonical_client_code(),
        )

        request = self.factory.get(
            "/auth-callback/",
            {"state": record.state, "access_token": "jwt", "refreshToken": "refresh"},
        )
        request.user = self.other_user

        response = angelone_callback(request)

        self.assertEqual(response.status_code, 403)
        self.assertIsNone(self.state_service.get(record.state))
        mock_register.assert_not_called()

    @mock.patch("main.angelone.services.auth_service.AuthService.register_existing_tokens")
    def test_callback_rejects_unexpected_query_params(self, mock_register):
        record = self.state_service.create(
            state="unexpected-param",
            user_id=self.user.id,
            broker_details_id=self.broker_details.id,
            client_code=self.broker_details.get_canonical_client_code(),
        )

        request = self.factory.get(
            "/auth-callback/",
            {"state": record.state, "access_token": "jwt", "refreshToken": "refresh", "evil": "1"},
        )
        request.user = self.user

        response = angelone_callback(request)

        self.assertEqual(response.status_code, 400)
        self.assertIn(b"Unexpected callback parameters", response.content)
        mock_register.assert_not_called()

    @mock.patch("main.angelone.services.auth_service.AuthService.register_existing_tokens")
    def test_callback_does_not_persist_tokens_before_verification(self, mock_register):
        record = self.state_service.create(
            state="verify-before-persist",
            user_id=self.user.id,
            broker_details_id=self.broker_details.id,
            client_code=self.broker_details.get_canonical_client_code(),
        )
        mock_register.return_value = {"status": "error", "message": "broker verification failed"}

        request = self.factory.get(
            "/auth-callback/",
            {"state": record.state, "access_token": "jwt", "refreshToken": "refresh", "feedToken": "feed"},
        )
        request.user = self.user

        response = angelone_callback(request)
        self.broker_details.refresh_from_db()

        self.assertEqual(response.status_code, 400)
        self.assertIsNone(self.broker_details.get_access_token_secure())
        self.assertIsNone(self.broker_details.get_refresh_token_secure())
        self.assertIsNone(self.broker_details.get_feed_token_secure())

    @mock.patch("main.angelone.services.auth_service.AuthService.register_existing_tokens")
    def test_callback_state_is_single_use_under_concurrency(self, mock_register):
        record = self.state_service.create(
            state="concurrent-replay",
            user_id=self.user.id,
            broker_details_id=self.broker_details.id,
            client_code=self.broker_details.get_canonical_client_code(),
        )
        mock_register.return_value = {"status": "success"}

        def consume_state():
            consumed = self.state_service.consume(record.state)
            return consumed.state if consumed else None

        with ThreadPoolExecutor(max_workers=2) as pool:
            consumed_states = list(pool.map(lambda _x: consume_state(), range(2)))

        self.assertEqual(sum(1 for item in consumed_states if item == record.state), 1)
        self.assertEqual(sum(1 for item in consumed_states if item is None), 1)


class AngelOneSerializerSecurityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="client@example.com",
            firstName="Client",
            lastName="User",
            phoneNumber="9999999993",
            password="Pass@1234",
        )
        self.broker = Broker.objects.create(broker_name="Angel One", is_active=True)
        self.broker_details = ClientBrokerdetails.objects.create(
            client=self.user,
            broker_name=self.broker,
            broker_API_KEY="public-key",
            broker_API_UID="B12345",
            broker_Demate_User_Name="B12345",
        )
        self.broker_details.set_broker_api_secret("secret-key")
        self.broker_details.set_broker_password("trading-password")
        self.broker_details.set_broker_totp_secret("BASE32SECRET")
        self.broker_details.set_session_tokens("jwt-token", "refresh-token", "feed-token")
        self.broker_details.save()

    def test_read_serializer_never_exposes_secrets(self):
        data = ClientBrokerDetailsSerializer(self.broker_details).data

        for forbidden_field in [
            "broker_API_SKEY",
            "broker_pass",
            "broker_Totp_Authcode",
            "access_token",
            "refreshToken",
            "feed_token",
            "encrypted_access_token",
            "encrypted_refresh_token",
            "encrypted_feed_token",
        ]:
            self.assertNotIn(forbidden_field, data)

        self.assertNotIn("buffer_percentage", data)
        self.assertNotIn("enable_market_orders", data)

        self.assertTrue(data["has_api_secret"])
        self.assertTrue(data["has_password"])
        self.assertTrue(data["has_totp_secret"])
        self.assertTrue(data["has_access_token"])
        self.assertTrue(data["has_refresh_token"])
        self.assertTrue(data["has_feed_token"])

    def test_partial_update_preserves_angelone_secrets(self):
        serializer = ClientBrokerDetailsUpdateSerializer(
            self.broker_details,
            data={"broker_Demate_User_Name": "B99999"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()

        self.assertEqual(instance.broker_Demate_User_Name, "B99999")
        self.assertEqual(instance.get_broker_password(), "trading-password")
        self.assertEqual(instance.get_broker_totp_secret(), "BASE32SECRET")
        self.assertEqual(instance.get_access_token_secure(), "jwt-token")

    def test_partial_update_encrypts_password_and_totp_for_future_fresh_login(self):
        serializer = ClientBrokerDetailsUpdateSerializer(
            self.broker_details,
            data={
                "broker_pass": "new-trading-password",
                "broker_Totp_Authcode": "NEWBASE32SECRET",
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()

        self.assertEqual(instance.get_broker_password(), "new-trading-password")
        self.assertEqual(instance.get_broker_totp_secret(), "NEWBASE32SECRET")
        self.assertTrue(bool(instance.encrypted_broker_password))
        self.assertTrue(bool(instance.encrypted_broker_totp_secret))
        self.assertIsNone(instance.broker_pass)
        self.assertIsNone(instance.broker_Totp_Authcode)

    def test_direct_model_save_promotes_raw_angelone_credentials_to_encrypted_fields(self):
        broker_details = ClientBrokerdetails.objects.create(
            client=self.user,
            broker_name=self.broker,
            broker_API_KEY="direct-key",
            broker_API_UID="DIR123",
            broker_Demate_User_Name="DIR123",
            broker_pass=" raw-password ",
            broker_Totp_Authcode=" RAWTOTPSECRET ",
        )

        broker_details.refresh_from_db()

        self.assertEqual(broker_details.get_broker_password(), "raw-password")
        self.assertEqual(broker_details.get_broker_totp_secret(), "RAWTOTPSECRET")
        self.assertTrue(bool(broker_details.encrypted_broker_password))
        self.assertTrue(bool(broker_details.encrypted_broker_totp_secret))
        self.assertIsNone(broker_details.broker_pass)
        self.assertIsNone(broker_details.broker_Totp_Authcode)

    def test_angle_one_alias_is_treated_as_angel_one_for_secure_persistence(self):
        alias_broker = Broker.objects.create(broker_name="Angle One", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.user,
            broker_name=alias_broker,
            broker_API_KEY="alias-key",
            broker_API_UID="ALIAS1",
            broker_Demate_User_Name="ALIAS1",
        )

        self.assertTrue(broker_details.is_angel_one_broker())

        serializer = ClientBrokerDetailsUpdateSerializer(
            broker_details,
            data={
                "broker_pass": "alias-password",
                "broker_Totp_Authcode": "ALIASTOTPSECRET",
            },
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()

        self.assertEqual(instance.get_broker_password(), "alias-password")
        self.assertEqual(instance.get_broker_totp_secret(), "ALIASTOTPSECRET")
        self.assertTrue(bool(instance.encrypted_broker_password))
        self.assertTrue(bool(instance.encrypted_broker_totp_secret))

    def test_read_serializer_includes_broker_setup_schema_and_available_brokers(self):
        data = ClientBrokerDetailsSerializer(self.broker_details).data

        self.assertEqual(data["selected_broker_name"], "Angel One")
        self.assertEqual(data["selected_broker_slug"], "angel-one")
        self.assertIsNotNone(data["broker_setup"])
        self.assertTrue(any(item["broker_name"] == "Angel One" for item in data["available_brokers"]))
        self.assertEqual(data["broker_setup"]["auth_mode"], "direct_credentials")
        schema_fields = {field["key"]: field for field in data["broker_setup"]["fields"]}
        self.assertTrue(schema_fields["broker_pass"]["configured"])
        self.assertTrue(schema_fields["broker_Totp_Authcode"]["configured"])
        self.assertEqual(schema_fields["broker_Demate_User_Name"]["value"], "B12345")

    def test_selection_only_update_allows_broker_switch_without_forcing_credentials(self):
        upstox = Broker.objects.create(broker_name="Upstox", is_active=True)
        serializer = ClientBrokerDetailsUpdateSerializer(
            self.broker_details,
            data={"broker_name": upstox.id},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        instance = serializer.save()
        self.assertEqual(instance.broker_name, upstox)

    def test_redirect_broker_requires_its_own_credentials_when_configuring(self):
        upstox = Broker.objects.create(broker_name="Upstox", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(client=self.user, broker_name=upstox)
        serializer = ClientBrokerDetailsUpdateSerializer(
            broker_details,
            data={"broker_API_KEY": "upstox-api-key"},
            partial=True,
        )
        self.assertFalse(serializer.is_valid())
        self.assertIn("broker_API_SKEY", serializer.errors)


class AngelOnePermissionTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.owner = User.objects.create_user(
            email="owner2@example.com",
            firstName="Owner",
            lastName="Two",
            phoneNumber="9999999994",
            password="Pass@1234",
        )
        self.other = User.objects.create_user(
            email="other2@example.com",
            firstName="Other",
            lastName="Two",
            phoneNumber="9999999995",
            password="Pass@1234",
        )
        self.broker = Broker.objects.create(broker_name="Angel One", is_active=True)
        self.broker_details = ClientBrokerdetails.objects.create(
            client=self.owner,
            broker_name=self.broker,
            broker_API_KEY="owner-key",
            broker_API_UID="C12345",
            broker_Demate_User_Name="C12345",
        )
        self.broker_details.set_broker_password("Pass@1234")
        self.broker_details.set_broker_totp_secret("JBSWY3DPEHPK3PXP")
        self.broker_details.save()

    def test_admin_broker_view_blocks_cross_client_access(self):
        request = self.factory.get(f"/get-client-broker-details-by-id/{self.owner.id}/")
        force_authenticate(request, user=self.other)

        response = AdminClientBrokerDetailsView.as_view()(request, pk=self.owner.id)

        self.assertEqual(response.status_code, 403)

    def test_angel_one_api_key_update_clears_stale_cached_sessions(self):
        session_manager = SessionManager.get_instance()
        session_manager.create_session_from_tokens(
            client_id="C12345",
            api_key="old-key",
            access_token="old-token",
            persist=True,
        )
        self.assertIsNotNone(session_manager.get_session("C12345", "old-key"))

        serializer = ClientBrokerDetailsUpdateSerializer(
            self.broker_details,
            data={"broker_API_KEY": "new-key"},
            partial=True,
        )
        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()

        self.assertIsNone(session_manager.get_session("C12345", "old-key"))
        self.broker_details.refresh_from_db()
        self.assertIsNone(self.broker_details.get_access_token_secure())


class LoginActivitySummaryTests(TestCase):
    def setUp(self):
        self.factory = APIRequestFactory()
        self.user = User.objects.create_user(
            email="activity@example.com",
            firstName="Activity",
            lastName="User",
            phoneNumber="9999999996",
            password="Pass@1234",
        )
        self.broker = Broker.objects.create(broker_name="Angel One", is_active=True)
        self.broker_details = ClientBrokerdetails.objects.create(
            client=self.user,
            broker_name=self.broker,
            broker_API_KEY="activity-key",
            broker_API_UID="ACT123",
            broker_Demate_User_Name="ACT123",
        )
        self.broker_details.set_session_tokens(
            "jwt-token",
            "refresh-token",
            "feed-token",
            expiry=timezone.now() + timezone.timedelta(hours=1),
            mark_token_created=True,
        )
        self.broker_details.broker_last_logout_at = timezone.now() - timezone.timedelta(minutes=15)
        self.broker_details.save()
        UserActivityLog.objects.create(
            user=self.user,
            last_login_time=timezone.now() - timezone.timedelta(hours=2),
            last_logout_time=timezone.now() - timezone.timedelta(hours=1, minutes=30),
            session_key="old-session",
        )
        UserActivityLog.objects.create(
            user=self.user,
            last_login_time=timezone.now() - timezone.timedelta(minutes=10),
            session_key="current-session",
        )

    @mock.patch("main.services.login_activity_service.SessionManager.get_instance")
    def test_login_activity_summary_returns_panel_and_broker_state(self, mock_get_instance):
        mock_session = mock.Mock()
        mock_session.is_valid.return_value = True
        mock_session.last_activity = timezone.now() - timezone.timedelta(minutes=1)
        mock_session.validated_at = timezone.now() - timezone.timedelta(minutes=2)
        mock_manager = mock.Mock()
        mock_manager.get_session.return_value = mock_session
        mock_get_instance.return_value = mock_manager

        current_iat = int((timezone.now() - timezone.timedelta(minutes=5)).timestamp())
        request = self.factory.get("/login-activity/")
        force_authenticate(request, user=self.user)

        response = LoginActivitySummaryView.as_view()(request)
        direct_summary = LoginActivityService().build_summary(
            self.user,
            request=SimpleNamespace(auth={"iat": current_iat}),
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertIsNotNone(response.data["data"]["panel"]["panel_login_time"])
        self.assertTrue(
            direct_summary["data"]["panel"]["current_panel_login_time"].startswith(
                timezone.datetime.fromtimestamp(current_iat, tz=timezone.utc).isoformat()[:16]
            )
        )
        self.assertIsNotNone(response.data["data"]["panel"]["previous_panel_login_time"])
        self.assertIsNotNone(response.data["data"]["panel"]["panel_logout_time"])
        self.assertEqual(response.data["data"]["broker"]["session"]["status"], "active")
        self.assertEqual(response.data["data"]["broker"]["token"]["status"], "active")
        self.assertIsNotNone(response.data["data"]["broker"]["last_login_at"])
        self.assertIsNotNone(response.data["data"]["broker"]["last_logout_at"])

    @mock.patch("main.services.login_activity_service.SessionManager.get_instance")
    def test_login_activity_summary_degrades_gracefully_when_session_store_is_unavailable(self, mock_get_instance):
        mock_manager = mock.Mock()
        mock_manager.get_session.side_effect = RuntimeError("redis unavailable")
        mock_get_instance.return_value = mock_manager

        request = self.factory.get("/login-activity/")
        force_authenticate(request, user=self.user)

        response = LoginActivitySummaryView.as_view()(request)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["status"], "success")
        self.assertEqual(response.data["data"]["broker"]["session"]["status"], "active")
        self.assertEqual(response.data["data"]["broker"]["session"]["source"], "persisted_recovery")
        self.assertEqual(response.data["data"]["broker"]["token"]["status"], "active")
        self.assertIsNotNone(response.data["data"]["panel"]["panel_login_time"])

    def test_login_activity_summary_ignores_legacy_plaintext_tokens(self):
        self.broker_details.encrypted_access_token = None
        self.broker_details.encrypted_refresh_token = None
        self.broker_details.encrypted_feed_token = None
        self.broker_details.access_token = "legacy-jwt-token"
        self.broker_details.refreshToken = "legacy-refresh-token"
        self.broker_details.feed_token = "legacy-feed-token"
        self.broker_details.save(
            update_fields=[
                "encrypted_access_token",
                "encrypted_refresh_token",
                "encrypted_feed_token",
                "access_token",
                "refreshToken",
                "feed_token",
            ]
        )

        summary = LoginActivityService().build_summary(self.user)

        self.assertEqual(summary["data"]["broker"]["token"]["status"], "unavailable")
        self.assertFalse(summary["data"]["broker"]["token"]["has_refresh_token"])
        self.assertFalse(summary["data"]["broker"]["token"]["has_feed_token"])


class PanelLoginTrackingTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(
            email="otpuser@example.com",
            firstName="Otp",
            lastName="User",
            phoneNumber="9999999997",
            password="Pass@1234",
            role=None,
            type_of_user="is_client",
            is_client=True,
            is_new_password=True,
        )

    def test_otp_verify_creates_current_session_log_with_session_key(self):
        otp = OTP.objects.create(user=self.user, is_verified=False)
        otp.otp_code = "123456"
        otp.expires_at = timezone.now() + timezone.timedelta(minutes=5)
        otp.save(update_fields=["otp_code", "expires_at"])

        request = self.factory.post("/verify-otp/", {"email": self.user.email, "otp_code": "123456"})
        middleware = SessionMiddleware(lambda req: None)
        middleware.process_request(request)
        request.session.save()

        serializer = OTPVerifySerializer(
            data={"email": self.user.email, "otp_code": "123456"},
            context={"request": request},
        )

        with mock.patch("main.serializers.get_client_ip", return_value="203.0.113.10"), \
             mock.patch("main.serializers.send_login_success_email.delay"):
            self.assertTrue(serializer.is_valid(), serializer.errors)
            serializer.validated_data

        latest_log = UserActivityLog.objects.filter(user=self.user).order_by("-last_login_time").first()
        self.assertIsNotNone(latest_log)
        self.assertIsNotNone(latest_log.session_key)
        self.assertIsNone(latest_log.last_logout_time)


class AngelOneSessionManagerTests(TestCase):
    def test_session_key_is_collision_safe(self):
        manager = SessionManager.get_instance()

        key_one = manager._get_session_key("client-a", "abcdefgh123")
        key_two = manager._get_session_key("client-a", "abcdefghXYZ")

        self.assertNotEqual(key_one, key_two)
        self.assertEqual(len(key_one), 64)

    def test_redis_payload_encrypts_broker_tokens(self):
        manager = SessionManager.get_instance()
        session = manager._build_session(
            client_id="client-a",
            api_key="api-key",
            access_token="jwt-token",
            refresh_token="refresh-token",
            feed_token="feed-token",
            source="test",
            validated=True,
        )

        payload = manager._payload_from_session(session)

        self.assertNotEqual(payload["api_key"], "api-key")
        self.assertNotEqual(payload["access_token"], "jwt-token")
        self.assertNotEqual(payload["refresh_token"], "refresh-token")
        self.assertNotEqual(payload["feed_token"], "feed-token")

    def test_refresh_invalid_token_sdk_type_error_returns_expired_session(self):
        manager = SessionManager.__new__(SessionManager)
        manager._persist_session = mock.Mock()
        manager._breaker = mock.Mock()
        smart_connect = SimpleNamespace(
            generateToken=mock.Mock(side_effect=TypeError("string indices must be integers, not 'str'"))
        )
        session = SimpleNamespace(
            refresh_token="expired-refresh",
            access_token="old-jwt",
            feed_token="old-feed",
            session_expiry=timezone.now(),
            status=SessionStatus.ACTIVE,
            smart_connect=smart_connect,
            can_refresh=lambda: True,
            attach_smart_connect=lambda: smart_connect,
        )

        response = manager._perform_refresh(session)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error_code"], "TOKEN_EXPIRED")
        self.assertIn("Please login again", response["message"])
        self.assertEqual(session.status, SessionStatus.INVALID)
        self.assertIsNone(session.access_token)
        self.assertIsNone(session.feed_token)

    def test_validate_session_propagates_expired_refresh_token(self):
        broker_details = SimpleNamespace(
            access_token_expiry=timezone.now() + timezone.timedelta(hours=1),
            get_access_token_secure=lambda: "old-access",
            get_refresh_token_secure=lambda: "old-refresh",
            get_feed_token_secure=lambda: "old-feed",
            get_angel_one_login_credentials=lambda: {
                "client_code": "A12345",
                "api_key": "angel-key",
                "password": None,
                "totp_secret": None,
            },
        )

        manager = SessionManager.get_instance()
        with (
            mock.patch.object(manager, "_get_cached_session", return_value=None),
            mock.patch.object(manager, "_remote_validate", return_value=False),
            mock.patch.object(
                manager,
                "_perform_refresh",
                return_value={
                    "status": "error",
                    "message": "Angel One session is invalid or expired. Please login again.",
                    "error_code": "TOKEN_EXPIRED",
                },
            ),
            mock.patch.object(manager, "invalidate_client_sessions") as mock_invalidate,
            mock.patch.object(manager, "_breaker") as mock_breaker,
        ):
            mock_breaker.is_open.return_value = False
            response = manager.validate_session("A12345", "angel-key", broker_details=broker_details)

        self.assertEqual(response["status"], "error")
        self.assertEqual(response["error_code"], "TOKEN_EXPIRED")
        mock_invalidate.assert_called_with("A12345")


class MigrationSafetyTests(TestCase):
    def test_client_trade_setting_migration_depends_on_initial(self):
        loader = MigrationLoader(connection)
        migration = loader.disk_migrations[("main", "0001_add_order_type_and_buffer_to_client_trade_setting")]
        self.assertIn(("main", "0001_initial"), migration.dependencies)


@override_settings(CACHES=TEST_CACHES)
class AngelOneExecutionValidationTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="angelone-validation@example.com",
            firstName="Angel",
            lastName="Validation",
            phoneNumber="9999999988",
            password="Pass@1234",
        )
        self.broker = Broker.objects.create(broker_name="Angel One", is_active=True)
        self.broker_details = ClientBrokerdetails.objects.create(
            client=self.user,
            broker_name=self.broker,
            broker_API_KEY="angel-key",
            broker_API_UID="A1420760",
            broker_Demate_User_Name="A1420760",
        )

    def _request(self, history_id="angel-history-1"):
        return ExecutionRequest(
            LivePrice=100,
            group_service="test",
            trade=SimpleNamespace(broker="Angel One", max_order_value=1000000),
            user=self.user,
            transaction_type="BUY",
            symbol="NIFTY",
            quantity=65,
            strategy="test-strategy",
            ordertype="LIMIT",
            product_type="INTRADAY",
            price=100,
            Lots=1,
            trade_order_status="ENTRY",
            Entry_type="BUY",
            Exit_type=None,
            Entry_price=None,
            Exit_price=None,
            EntryQty=65,
            ExitQty=None,
            webhook_signal={},
            Exchange="NFO",
            Segment="OPT",
            Index_Symbol="NIFTY",
            triggerPrice=None,
            day="19",
            month="May",
            year="26",
            fullyear="2026",
            strike=23700,
            option_type="PE",
            order_params={"quantity": 65},
            history_id=history_id,
            contract_info=ContractInfo(
                symbol="NIFTY",
                strike=23700,
                option_type="PE",
                exchange="NFO",
                expiry=datetime(2026, 5, 19),
            ),
        )

    def test_zero_like_limit_price_is_treated_as_auto_buffer_price(self):
        request = self._request()
        request = ExecutionRequest(
            **{
                **request.__dict__,
                "price": "0.0",
                "order_params": {
                    **request.order_params,
                    "price": "0.0",
                    "ordertype": "LIMIT",
                    "order_type": "LIMIT",
                },
            }
        )
        engine = ExecutionEngine.__new__(ExecutionEngine)
        engine._auth_service = mock.Mock()
        engine._auth_service.ensure_valid_session.return_value = {
            "status": "success",
            "session": SimpleNamespace(smart_connect=mock.Mock()),
        }
        engine._contract_manager = mock.Mock()
        engine._contract_manager.initialize.return_value = None
        engine._contract_manager.resolve_option_contract.return_value = (
            Contract(
                token="12345",
                symbol="NIFTY19MAY2623700PE",
                name="NIFTY",
                expiry=datetime(2026, 5, 19),
                strike=23700,
                lot_size=65,
                instrument_type="OPTIDX",
                exchange="NFO",
                tick_size=0.05,
                option_type="PE",
            ),
            {"tradingsymbol": "NIFTY19MAY2623700PE", "expiry": "2026-05-19"},
        )
        engine._ltp_service = mock.Mock()
        engine._ltp_service.get_ltp.return_value = 100
        engine._ltp_service.calculate_limit_price.return_value = 102.5
        engine._get_client_broker = mock.Mock(return_value=self.broker_details)

        fixed_now = datetime(2026, 5, 19, 14, 37, tzinfo=ZoneInfo(TIMEZONE))
        with mock.patch("main.execution_engine.datetime", wraps=datetime) as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            result = engine._validate_angel_one_request(request)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["validated_price"], 102.5)
        engine._ltp_service.calculate_limit_price.assert_called_once()
        engine._ltp_service.round_to_tick.assert_not_called()

    def test_auto_buffer_price_does_not_fail_slippage_guard(self):
        request = self._request()
        request = ExecutionRequest(
            **{
                **request.__dict__,
                "price": None,
                "order_params": {
                    **request.order_params,
                    "ordertype": "LIMIT",
                    "order_type": "LIMIT",
                },
            }
        )
        engine = ExecutionEngine.__new__(ExecutionEngine)
        engine._auth_service = mock.Mock()
        engine._auth_service.ensure_valid_session.return_value = {
            "status": "success",
            "session": SimpleNamespace(smart_connect=mock.Mock()),
        }
        engine._contract_manager = mock.Mock()
        engine._contract_manager.initialize.return_value = None
        engine._contract_manager.resolve_option_contract.return_value = (
            Contract(
                token="12345",
                symbol="NIFTY19MAY2623700PE",
                name="NIFTY",
                expiry=datetime(2026, 5, 19),
                strike=23700,
                lot_size=65,
                instrument_type="OPTIDX",
                exchange="NFO",
                tick_size=0.05,
                option_type="PE",
            ),
            {"tradingsymbol": "NIFTY19MAY2623700PE", "expiry": "2026-05-19"},
        )
        engine._ltp_service = mock.Mock()
        engine._ltp_service.get_ltp.return_value = 100
        engine._ltp_service.calculate_limit_price.return_value = 120
        engine._get_client_broker = mock.Mock(return_value=self.broker_details)

        fixed_now = datetime(2026, 5, 19, 14, 37, tzinfo=ZoneInfo(TIMEZONE))
        with mock.patch("main.execution_engine.datetime", wraps=datetime) as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            result = engine._validate_angel_one_request(request)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["validated_price"], 120)

    def test_angel_one_order_service_treats_zero_like_price_as_missing(self):
        self.assertIsNone(angel_one_optional_price("0.0"))
        self.assertIsNone(angel_one_optional_price("0.00"))
        self.assertIsNone(angel_one_optional_price(0))
        self.assertEqual(angel_one_optional_price("101.25"), 101.25)

    def test_same_day_midnight_contract_expiry_is_tradable_until_market_close(self):
        engine = ExecutionEngine.__new__(ExecutionEngine)
        engine._auth_service = mock.Mock()
        engine._auth_service.ensure_valid_session.return_value = {
            "status": "success",
            "session": SimpleNamespace(smart_connect=mock.Mock()),
        }
        engine._contract_manager = mock.Mock()
        engine._contract_manager.initialize.return_value = None
        engine._contract_manager.resolve_option_contract.return_value = (
            Contract(
                token="12345",
                symbol="NIFTY19MAY2623700PE",
                name="NIFTY",
                expiry=datetime(2026, 5, 19),
                strike=23700,
                lot_size=65,
                instrument_type="OPTIDX",
                exchange="NFO",
                tick_size=0.05,
                option_type="PE",
            ),
            {"tradingsymbol": "NIFTY19MAY2623700PE", "expiry": "2026-05-19"},
        )
        engine._ltp_service = mock.Mock()
        engine._ltp_service.get_ltp.return_value = 100
        engine._ltp_service.round_to_tick.return_value = 100
        engine._get_client_broker = mock.Mock(return_value=self.broker_details)

        fixed_now = datetime(2026, 5, 19, 14, 37, tzinfo=ZoneInfo(TIMEZONE))
        with mock.patch("main.execution_engine.datetime", wraps=datetime) as mock_datetime:
            mock_datetime.now.return_value = fixed_now
            result = engine._validate_angel_one_request(self._request())

        self.assertEqual(result["status"], "success")

    def test_midnight_contract_expiry_cutoff_uses_market_close(self):
        engine = ExecutionEngine.__new__(ExecutionEngine)

        cutoff = engine._normalize_contract_expiry_cutoff(datetime(2026, 5, 19))

        self.assertEqual(cutoff.hour, MARKET_CLOSE_HOUR)
        self.assertEqual(cutoff.minute, MARKET_CLOSE_MINUTE)
        self.assertEqual(cutoff.tzinfo, ZoneInfo(TIMEZONE))

    def test_validation_failure_updates_trade_history_placeholder(self):
        request = self._request(history_id="angel-history-validation-failure")
        placeholder = "Order is placing by place order broker !!"
        save_trade_order_history(
            100,
            "test",
            "BUY",
            "ENTRY",
            self.user,
            None,
            0,
            "Failed",
            placeholder,
            placeholder,
            "test-strategy",
            "BUY",
            None,
            None,
            None,
            65,
            None,
            {},
            "NFO",
            "OPT",
            "NIFTY",
            {"quantity": 65},
            broker=None,
            history_id=request.history_id,
        )
        engine = ExecutionEngine.__new__(ExecutionEngine)
        response = {
            "data": {
                "status": "Failed",
                "message": "Resolved contract has already expired and cannot be traded.",
                "error_code": "CONTRACT_EXPIRED",
            }
        }

        engine._record_validation_failure_history(
            request,
            response,
            {"contract_match": {"tradingsymbol": "NIFTY19MAY2623700PE"}},
        )

        history = Tradeorderhistory.objects.get(history_id=request.history_id)
        self.assertEqual(history.failure_reason, response["data"]["message"])
        self.assertEqual(history.response_data["data"]["error_code"], "CONTRACT_EXPIRED")
        self.assertEqual(history.broker, "Angel One")

    def test_dispatch_routes_angel_one_through_execution_node_proxy(self):
        request = self._request()
        engine = ExecutionEngine.__new__(ExecutionEngine)
        engine._execute_angel_one = mock.Mock()
        engine._route_to_execution_node_if_configured = mock.Mock(
            return_value={"status": "proxy_routing", "job_id": 1, "message": ""}
        )

        response = engine._dispatch(request, {"client_broker": self.broker_details})

        self.assertEqual(response["status"], "proxy_routing")
        engine._route_to_execution_node_if_configured.assert_called_once_with(request, {"client_broker": self.broker_details})
        engine._execute_angel_one.assert_not_called()

    def test_dispatch_keeps_proxy_requirement_for_non_angel_brokers(self):
        request = self._request()
        request = ExecutionRequest(
            **{
                **request.__dict__,
                "trade": SimpleNamespace(broker="Alice Blue", max_order_value=1000000),
            }
        )
        engine = ExecutionEngine.__new__(ExecutionEngine)
        engine._execute_angel_one = mock.Mock()
        engine._route_to_execution_node_if_configured = mock.Mock(
            return_value={"data": {"status": "Failed", "message": "No verified execution node/proxy is assigned. Direct broker execution is blocked."}}
        )

        response = engine._dispatch(request, {})

        self.assertEqual(response["data"]["status"], "Failed")
        engine._route_to_execution_node_if_configured.assert_called_once_with(request, {})
        engine._execute_angel_one.assert_not_called()

    def test_order_service_structured_failure_keeps_original_message(self):
        service = OrderService.__new__(OrderService)

        response = service._error_response(
            "Broker rejected order",
            "request-1",
            **{key: value for key, value in {"message": "Broker rejected order", "error_code": "ORDER_EXECUTION_FAILED"}.items() if key != "message"},
        )

        self.assertEqual(response["message"], "Broker rejected order")
        self.assertEqual(response["error_code"], "ORDER_EXECUTION_FAILED")

    def test_order_service_maps_empty_smartapi_response_to_safe_message(self):
        service = OrderService.__new__(OrderService)

        response = service._build_error_payload("Couldn't parse the JSON response received from the server: b''")

        self.assertEqual(response["error_code"], "EMPTY_BROKER_RESPONSE")
        self.assertIn("check the Angel One order book before retrying", response["message"])

    def test_order_service_maps_smartapi_timeout_to_unconfirmed_message(self):
        service = OrderService.__new__(OrderService)

        response = service._build_error_payload(
            "HTTPSConnectionPool(host='apiconnect.angelone.in', port=443): Read timed out. (read timeout=7)"
        )

        self.assertEqual(response["error_code"], "BROKER_TIMEOUT_UNCONFIRMED")
        self.assertIn("verify the broker order book before retrying", response["message"])

    def test_order_service_finds_matching_order_for_timeout_reconciliation(self):
        service = OrderService.__new__(OrderService)

        smart_connect = mock.Mock()
        smart_connect.orderBook.return_value = {
            "status": True,
            "data": [
                {
                    "orderid": "old-order",
                    "tradingsymbol": "NIFTY26MAY2624000CE",
                    "symboltoken": "111",
                    "transactiontype": "BUY",
                    "exchange": "NFO",
                    "producttype": "INTRADAY",
                    "ordertype": "LIMIT",
                    "quantity": "65",
                    "price": "40.00",
                },
                {
                    "orderid": "matched-order",
                    "tradingsymbol": "NIFTY26MAY2624100CE",
                    "symboltoken": "222",
                    "transactiontype": "BUY",
                    "exchange": "NFO",
                    "producttype": "INTRADAY",
                    "ordertype": "LIMIT",
                    "quantity": "65",
                    "price": "40.00",
                },
            ],
        }

        order = service._find_matching_broker_order(
            smart_connect,
            {
                "tradingsymbol": "NIFTY26MAY2624100CE",
                "symboltoken": "222",
                "transactiontype": "BUY",
                "exchange": "NFO",
                "producttype": "INTRADAY",
                "ordertype": "LIMIT",
                "quantity": "65",
                "price": "40.0",
            },
        )

        self.assertEqual(order["orderid"], "matched-order")

    def test_order_service_normalizes_product_type_aliases_for_angel_one(self):
        service = OrderService.__new__(OrderService)

        self.assertEqual(service._normalize_product_type("MIS"), "INTRADAY")
        self.assertEqual(service._normalize_product_type("NRML"), "CARRYFORWARD")
        self.assertEqual(service._normalize_product_type("CNC"), "DELIVERY")


class SecretLeakageTests(TestCase):
    def test_sensitive_print_statements_are_absent_from_hardened_paths(self):
        backend_root = Path(__file__).resolve().parents[2]
        files_to_check = [
            backend_root / "main" / "serializers.py",
            backend_root / "main" / "views.py",
            backend_root / "main" / "dematemodule.py",
            backend_root / "main" / "upstock.py",
        ]
        forbidden = re.compile(
            r"(?m)^\s*print\s*\(.*(password|pass|access_token|refresh_token|feed_token|auth_code|client_key|secret)",
            re.IGNORECASE,
        )

        for path in files_to_check:
            self.assertIsNone(
                forbidden.search(path.read_text()),
                f"Sensitive print/logging statement remains in {path}",
            )


class SettingsValidationTests(TestCase):
    def test_production_settings_fail_fast_without_required_security_env(self):
        backend_root = Path(__file__).resolve().parents[2]
        env = os.environ.copy()
        env["APP_ENV"] = "production"
        env.pop("DJANGO_SECRET_KEY", None)
        env.pop("BROKER_ENCRYPTION_KEYS", None)
        env["DB_ENGINE"] = "django.db.backends.postgresql"
        env["DB_NAME"] = "algoview"
        env["ALLOWED_HOSTS"] = "trade.example.com"

        result = subprocess.run(
            [
                str(backend_root / "venv" / "bin" / "python"),
                "-c",
                "import algoview.settings",
            ],
            cwd=str(backend_root),
            env=env,
            capture_output=True,
            text=True,
        )

        self.assertNotEqual(result.returncode, 0)
        self.assertIn("DJANGO_SECRET_KEY must be configured", result.stderr)
