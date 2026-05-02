from unittest import mock

from django.core.management import call_command, CommandError
from django.test import TestCase
from io import StringIO

from main.angelone.services.validation_harness import AngelOneValidationHarness
from main.models import Broker, ClientBrokerdetails, User


class AngelOneValidationHarnessTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="harness@example.com",
            firstName="Harness",
            lastName="User",
            phoneNumber="9999999988",
            password="Pass@1234",
        )
        self.broker = Broker.objects.create(broker_name="Angel One", is_active=True)
        self.broker_details = ClientBrokerdetails.objects.create(
            client=self.user,
            broker_name=self.broker,
            broker_API_KEY="api-key",
            broker_API_UID="VAL123",
            broker_Demate_User_Name="VAL123",
        )
        self.broker_details.set_broker_password("password123")
        self.broker_details.set_broker_totp_secret("JBSWY3DPEHPK3PXP")
        self.broker_details.save()
        self.harness = AngelOneValidationHarness()

    def test_resolve_broker_details_by_client_code(self):
        resolved = self.harness.resolve_broker_details(client_code="VAL123")
        self.assertEqual(resolved.id, self.broker_details.id)

    @mock.patch("main.angelone.services.validation_harness.AuthService.login")
    @mock.patch("main.angelone.services.validation_harness.AuthService.get_session")
    def test_login_flow_result_shape(self, mock_get_session, mock_login):
        mock_login.return_value = {"status": "success", "message": "ok"}
        mock_session = mock.Mock()
        mock_session.access_token = "jwt"
        mock_session.refresh_token = "refresh"
        mock_session.feed_token = "feed"
        mock_session.status.value = "active"
        mock_get_session.return_value = mock_session

        result = self.harness.test_login_flow(self.broker_details)

        self.assertTrue(result.passed)
        self.assertEqual(result.name, "login_flow")

    @mock.patch("main.angelone.services.validation_harness.AuthService.login")
    @mock.patch("main.angelone.services.validation_harness.AuthService.get_session")
    def test_login_flow_passes_when_login_succeeds_with_resolved_credentials(self, mock_get_session, mock_login):
        self.broker_details.encrypted_broker_password = None
        self.broker_details.encrypted_broker_totp_secret = None
        self.broker_details.broker_pass = "legacy-password"
        self.broker_details.broker_Totp_Authcode = "LEGACYTOTPSECRET"

        mock_login.return_value = {"status": "success", "message": "ok"}
        mock_session = mock.Mock()
        mock_session.access_token = "jwt"
        mock_session.refresh_token = "refresh"
        mock_session.feed_token = "feed"
        mock_session.status.value = "active"
        mock_get_session.return_value = mock_session

        result = self.harness.test_login_flow(self.broker_details)

        self.assertTrue(result.passed)
        self.assertTrue(result.details["has_password"])
        self.assertTrue(result.details["has_totp"])

    @mock.patch("main.angelone.services.validation_harness.AuthService.ensure_valid_session")
    @mock.patch("main.angelone.services.validation_harness.AuthService.get_session")
    def test_login_flow_passes_by_reusing_valid_session_when_credentials_are_not_resolved(self, mock_get_session, mock_ensure):
        self.broker_details.encrypted_broker_password = None
        self.broker_details.encrypted_broker_totp_secret = None
        self.broker_details.broker_pass = None
        self.broker_details.broker_Totp_Authcode = None

        mock_session = mock.Mock()
        mock_session.access_token = "jwt"
        mock_session.refresh_token = "refresh"
        mock_session.feed_token = "feed"
        mock_session.status.value = "active"
        mock_ensure.return_value = {"status": "success", "source": "redis", "session": mock_session}
        mock_get_session.return_value = mock_session

        result = self.harness.test_login_flow(self.broker_details)

        self.assertTrue(result.passed)
        self.assertFalse(result.details["attempted_fresh_login"])
        self.assertEqual(result.details["validation_source"], "redis")
        self.assertFalse(result.details["has_password"])
        self.assertFalse(result.details["has_totp"])

    def test_failure_injection_invalid_credentials(self):
        with mock.patch("main.angelone.services.validation_harness.AuthService.login", return_value={"status": "error", "message": "Invalid credentials"}):
            result = self.harness.test_failure_injection(self.broker_details, "invalid_credentials")
        self.assertTrue(result.passed)

    def test_login_flow_uses_plaintext_fallback_credentials(self):
        self.broker_details.encrypted_broker_password = None
        self.broker_details.encrypted_broker_totp_secret = None
        self.broker_details.broker_pass = " legacy-password "
        self.broker_details.broker_Totp_Authcode = " LEGACYTOTPSECRET "

        self.assertEqual(self.broker_details.get_broker_password(), "legacy-password")
        self.assertEqual(self.broker_details.get_broker_totp_secret(), "LEGACYTOTPSECRET")
        credentials = self.broker_details.get_angel_one_login_credentials()
        self.assertEqual(credentials["password"], "legacy-password")
        self.assertEqual(credentials["totp_secret"], "LEGACYTOTPSECRET")

    @mock.patch("main.angelone.services.validation_harness.AuthService.login")
    @mock.patch("main.angelone.services.validation_harness.AuthService.get_session")
    def test_login_flow_uses_plaintext_fallback_credentials_when_encrypted_fields_are_empty(self, mock_get_session, mock_login):
        self.broker_details.encrypted_broker_password = None
        self.broker_details.encrypted_broker_totp_secret = None
        self.broker_details.broker_pass = " legacy-password "
        self.broker_details.broker_Totp_Authcode = " LEGACYTOTPSECRET "

        mock_login.return_value = {"status": "success", "message": "ok"}
        mock_session = mock.Mock()
        mock_session.access_token = "jwt"
        mock_session.refresh_token = "refresh"
        mock_session.feed_token = "feed"
        mock_session.status.value = "active"
        mock_get_session.return_value = mock_session

        result = self.harness.test_login_flow(self.broker_details)

        self.assertTrue(result.passed)
        _, kwargs = mock_login.call_args
        self.assertEqual(kwargs["password"], "legacy-password")
        self.assertEqual(kwargs["totp_secret"], "LEGACYTOTPSECRET")

    def test_check_prerequisites_returns_error_on_redis_failure(self):
        with mock.patch.object(self.harness.session_manager._redis, "ping", side_effect=ConnectionError("redis down")):
            result = self.harness.check_prerequisites()

        self.assertEqual(result["status"], "error")
        self.assertEqual(result["checks"][0]["name"], "redis_session_store")
        self.assertFalse(result["checks"][0]["success"])
        self.assertIn("hints", result["checks"][0])
        self.assertIn("Configured Redis target", result["checks"][0]["hints"][0])

    @mock.patch("main.management.commands.validate_angelone_live.AngelOneValidationHarness.check_prerequisites")
    def test_validate_command_reports_redis_hints(self, mock_check_prerequisites):
        mock_check_prerequisites.return_value = {
            "status": "error",
            "context": {"redis_url": "redis://redis.internal:6379/1"},
            "checks": [
                {
                    "name": "redis_session_store",
                    "success": False,
                    "error": "Error 61 connecting to redis.internal:6379. Connection refused.",
                    "hints": [
                        "Configured Redis target: redis://redis.internal:6379/1",
                        "Make sure a Redis server is listening on the configured host and port.",
                    ],
                }
            ],
            "failure_count": 1,
        }

        with self.assertRaises(CommandError) as exc:
            call_command("validate_angelone_live", client_code="VAL123")

        self.assertIn("Connection refused", str(exc.exception))
        self.assertIn("Configured Redis target", str(exc.exception))

    @mock.patch("main.management.commands.check_angelone_dependencies.AngelOneValidationHarness.check_prerequisites")
    def test_dependency_check_command_reports_redis_hints(self, mock_check_prerequisites):
        mock_check_prerequisites.return_value = {
            "status": "error",
            "context": {"redis_url": "redis://redis.internal:6379/1"},
            "checks": [
                {
                    "name": "redis_session_store",
                    "success": False,
                    "error": "Error 61 connecting to redis.internal:6379. Connection refused.",
                    "hints": [
                        "Configured Redis target: redis://redis.internal:6379/1",
                        "Verify connectivity with: redis-cli -u redis://redis.internal:6379/1 ping",
                    ],
                }
            ],
            "failure_count": 1,
        }
        stdout = StringIO()

        with self.assertRaises(CommandError) as exc:
            call_command("check_angelone_dependencies", stdout=stdout)

        output = stdout.getvalue()
        self.assertIn("redis://redis.internal:6379/1", output)
        self.assertIn("Connection refused", str(exc.exception))
        self.assertIn("redis-cli -u redis://redis.internal:6379/1 ping", str(exc.exception))
