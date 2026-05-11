from types import SimpleNamespace
from unittest import mock

from django.test import TestCase, override_settings
from django.urls import Resolver404, resolve

from main.angelone.services.state_service import CallbackStateService
from main.models import Broker, ClientBrokerdetails, ExecutionNode, User


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
    def _attach_verified_proxy(self, broker_details, *, node_id="callback-node"):
        node = ExecutionNode.objects.create(
            name=node_id,
            ip_address="203.0.113.10",
            provider="Test",
            node_id=node_id,
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=False,
            assigned_client=broker_details.client,
            status=ExecutionNode.STATUS_ASSIGNED,
        )
        broker_details.execution_node = node
        broker_details.save(update_fields=["execution_node"])
        return node

    def test_broker_callback_fails_closed_for_unknown_request_token(self):
        response = self.client.get("/api/broker/callback/", {"request_token": "test123"})

        self.assertEqual(response.status_code, 400)
        payload = response.json()
        self.assertEqual(payload["message"], "Failed")
        self.assertIn("callback state", payload["error"])
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
        self._attach_verified_proxy(broker_details, node_id="upstox-callback-node")
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
        self._attach_verified_proxy(broker_details, node_id="upstox-browser-node")
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

    @mock.patch("main.dematemodule.requests.get")
    def test_dhan_token_id_callback_is_exchanged_without_state(self, mock_get):
        user = User.objects.create_user(
            email="dhan-owner@example.com",
            firstName="Dhan",
            lastName="Owner",
            phoneNumber="9999999996",
            password="Pass@1234",
        )
        broker = Broker.objects.create(broker_name="Dhan", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=user,
            broker_name=broker,
            broker_API_KEY="dhan-app-id",
            broker_API_SKEY="dhan-secret",
            broker_API_UID="1100000011",
            request_token="consent-app-id",
        )
        self._attach_verified_proxy(broker_details, node_id="dhan-callback-node")
        mock_get.return_value = SimpleNamespace(
            status_code=200,
            content=b"{}",
            json=lambda: {
                "accessToken": "dhan-access-token",
                "dhanClientId": "1100000011",
                "expiryTime": "2026-05-11T15:30:00+05:30",
            },
        )

        response = self.client.get("/api/broker/callback/", {"tokenId": "dhan-token-id"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "success")
        mock_get.assert_called_once()
        broker_details.refresh_from_db()
        self.assertEqual(broker_details.access_token, "dhan-access-token")

    @mock.patch("main.dematemodule.KiteConnect")
    def test_zerodha_request_token_callback_is_exchanged_without_state(self, mock_kite_class):
        user = User.objects.create_user(
            email="zerodha-owner@example.com",
            firstName="Zerodha",
            lastName="Owner",
            phoneNumber="9999999995",
            password="Pass@1234",
        )
        broker = Broker.objects.create(broker_name="Zerodha", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=user,
            broker_name=broker,
            broker_API_KEY="kite-api",
            broker_API_SKEY="kite-secret",
            request_token="zerodha-login-state",
        )
        self._attach_verified_proxy(broker_details, node_id="zerodha-callback-node")
        kite = mock_kite_class.return_value
        kite.generate_session.return_value = {"access_token": "kite-access-token"}

        response = self.client.get(
            "/api/broker/callback/",
            {
                "action": "login",
                "type": "login",
                "status": "success",
                "request_token": "kite-request-token",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "success")
        mock_kite_class.assert_called_once_with(
            api_key="kite-api",
            proxies={
                "http": "http://proxy.example.com:8080",
                "https": "http://proxy.example.com:8080",
            },
        )
        kite.generate_session.assert_called_once_with("kite-request-token", api_secret="kite-secret")
        broker_details.refresh_from_db()
        self.assertEqual(broker_details.access_token, "kite-access-token")
