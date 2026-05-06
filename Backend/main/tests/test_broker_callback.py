from types import SimpleNamespace
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import Resolver404, resolve

from main.angelone.services.state_service import CallbackStateService
from main.models import Broker, ClientBrokerdetails, User


TEST_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "broker-callback-tests"},
    "circuit_breaker": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "broker-callback-circuit"},
}


@override_settings(
    CACHES=TEST_CACHES,
    ANGELONE_STATE_CACHE_PREFIX="test:broker-callback:state",
    ANGELONE_CALLBACK_STATE_TTL_SECONDS=60,
)
class BrokerCallbackRoutingTests(TestCase):
    def test_broker_callback_accepts_request_token(self):
        response = self.client.get("/api/broker/callback/", {"request_token": "test123"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["message"], "Broker callback received.")
        self.assertIn("request_token", payload["callback"]["present_params"])
        self.assertNotIn("test123", str(payload))

    def test_broker_callback_final_url_is_not_double_prefixed(self):
        match = resolve("/api/broker/callback/")
        self.assertEqual(match.url_name, "broker-callback")

        with self.assertRaises(Resolver404):
            resolve("/api/api/broker/callback/")

    def test_broker_callback_missing_params_returns_safe_json(self):
        response = self.client.get("/api/broker/callback/")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "success")
        self.assertEqual(payload["callback"]["present_params"], [])
        self.assertEqual(payload["callback"]["token_exchange"], "not_attempted")

    @mock.patch("main.dematemodule.requests.post")
    def test_broker_callback_with_state_exchanges_upstox_token(self, mock_post):
        user = User.objects.create_user(
            email="upstox-owner@example.com",
            firstName="Upstox",
            lastName="Owner",
            phoneNumber="9999999998",
            password="Pass@1234",
        )
        broker = Broker.objects.create(broker_name="Upstox", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=user,
            broker_name=broker,
            broker_API_KEY="upstox-key",
            broker_API_SKEY="upstox-secret",
        )
        CallbackStateService().create(
            state="upstox-state",
            user_id=user.id,
            broker_details_id=broker_details.id,
            client_code="upstox-client",
        )
        mock_post.return_value = SimpleNamespace(
            status_code=200,
            content=b"{}",
            json=lambda: {
                "access_token": "upstox-access",
                "refresh_token": "upstox-refresh",
                "expires_in": 3600,
            },
        )

        response = self.client.get("/api/broker/callback/", {"code": "upstox-code", "state": "upstox-state"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "success")
        mock_post.assert_called_once()
        broker_details.refresh_from_db()
        self.assertEqual(broker_details.access_token, "upstox-access")

    @mock.patch("main.dematemodule.requests.post")
    def test_browser_broker_callback_redirects_without_token_json(self, mock_post):
        user = User.objects.create_user(
            email="upstox-browser@example.com",
            firstName="Browser",
            lastName="Owner",
            phoneNumber="9999999997",
            password="Pass@1234",
        )
        broker = Broker.objects.create(broker_name="Upstox", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=user,
            broker_name=broker,
            broker_API_KEY="upstox-key",
            broker_API_SKEY="upstox-secret",
        )
        CallbackStateService().create(
            state="browser-state",
            user_id=user.id,
            broker_details_id=broker_details.id,
            client_code="upstox-client",
            frontend_redirect_url="https://app.sparkstechnologies.co.in/dashboard/algoviewtech/user",
        )
        mock_post.return_value = SimpleNamespace(
            status_code=200,
            content=b"{}",
            json=lambda: {"access_token": "browser-access", "refresh_token": "browser-refresh"},
        )

        response = self.client.get(
            "/api/broker/callback/",
            {"code": "upstox-code", "state": "browser-state"},
            HTTP_ACCEPT="text/html,application/xhtml+xml",
        )

        self.assertEqual(response.status_code, 302)
        self.assertIn("/dashboard/algoviewtech/user", response["Location"])
        self.assertIn("broker_login=success", response["Location"])
        self.assertNotIn("browser-access", response["Location"])
