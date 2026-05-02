import os
import re
import subprocess
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest import mock
from types import SimpleNamespace

from django.contrib.sessions.middleware import SessionMiddleware
from django.db import connection
from django.db.migrations.loader import MigrationLoader
from django.test import RequestFactory, TestCase, override_settings
from rest_framework.test import APIRequestFactory, force_authenticate

from main.angelone.managers.session_manager import SessionManager
from main.angelone.services.state_service import CallbackStateService
from main.angelone_views import angelone_callback
from main.models import Broker, ClientBrokerdetails, OTP, User, UserActivityLog
from main.serializers import ClientBrokerDetailsSerializer, ClientBrokerDetailsUpdateSerializer, OTPVerifySerializer
from main.services.login_activity_service import LoginActivityService
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

    def test_admin_broker_view_blocks_cross_client_access(self):
        request = self.factory.get(f"/get-client-broker-details-by-id/{self.owner.id}/")
        force_authenticate(request, user=self.other)

        response = AdminClientBrokerDetailsView.as_view()(request, pk=self.owner.id)

        self.assertEqual(response.status_code, 403)


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


class MigrationSafetyTests(TestCase):
    def test_client_trade_setting_migration_depends_on_initial(self):
        loader = MigrationLoader(connection)
        migration = loader.disk_migrations[("main", "0001_add_order_type_and_buffer_to_client_trade_setting")]
        self.assertIn(("main", "0001_initial"), migration.dependencies)


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
