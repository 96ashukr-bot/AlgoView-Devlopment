from types import SimpleNamespace
from unittest import mock

from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone

from main.brokers.base import get_broker_adapter
from main.models import Broker, ClientBrokerdetails, ExecutionNode, ExecutionOrderJob, User
from main.services.execution_nodes import assign_execution_node_to_client, release_execution_node
from main.services.execution_router import route_order_to_execution_node
from main.services.node_security import generate_node_signature, verify_node_signature


TEST_CACHES = {
    "default": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "execution-node-tests"},
    "circuit_breaker": {"BACKEND": "django.core.cache.backends.locmem.LocMemCache", "LOCATION": "execution-node-circuit"},
}


@override_settings(
    CACHES=TEST_CACHES,
    NODE_REQUEST_TIMEOUT=1,
    NODE_ALLOWED_CLOCK_SKEW_SECONDS=60,
    ALGOVIEW_NODE_SECRET="node-secret",
    ALGOVIEW_NODE_ID="node-1",
)
class ExecutionNodeManagerTests(TestCase):
    def setUp(self):
        cache.clear()
        self.client_user = User.objects.create_user(
            email="client@example.com",
            firstName="Client",
            lastName="One",
            phoneNumber="9999999999",
            password="Pass@123",
            is_enable=True,
        )
        self.other_client = User.objects.create_user(
            email="client2@example.com",
            firstName="Client",
            lastName="Two",
            phoneNumber="9999999998",
            password="Pass@123",
        )
        self.broker = Broker.objects.create(broker_name="Angel One", is_active=True)
        self.broker_details = ClientBrokerdetails.objects.create(client=self.client_user, broker_name=self.broker, broker_API_KEY="key", broker_Demate_User_Name="A1")
        self.node = ExecutionNode.objects.create(
            name="Node 1",
            ip_address="10.0.0.10",
            provider="aws",
            server_url="https://node.example.com",
            node_id="node-1",
            is_verified_with_broker=True,
        )
        self.node.set_node_secret("node-secret")
        self.node.save(update_fields=["node_secret"])

    def test_duplicate_ip_prevention(self):
        with self.assertRaises(Exception):
            ExecutionNode.objects.create(
                name="Node 2",
                ip_address="10.0.0.10",
                provider="aws",
                server_url="https://node2.example.com",
                node_id="node-2",
            )

    def test_assign_and_release_node(self):
        assign_execution_node_to_client(self.client_user, self.node)
        self.node.refresh_from_db()
        self.broker_details.refresh_from_db()
        self.assertEqual(self.node.assigned_client_id, self.client_user.id)
        self.assertEqual(self.broker_details.execution_node_id, self.node.id)

        release_execution_node(self.client_user)
        self.node.refresh_from_db()
        self.assertIsNone(self.node.assigned_client_id)

    def test_one_node_one_client_rule(self):
        assign_execution_node_to_client(self.client_user, self.node)
        with self.assertRaises(ValidationError):
            assign_execution_node_to_client(self.other_client, self.node)

    def test_block_order_without_verified_node(self):
        assign_execution_node_to_client(self.client_user, self.node)
        self.node.is_verified_with_broker = False
        self.node.save(update_fields=["is_verified_with_broker"])
        self.broker_details.refresh_from_db()
        with self.assertRaises(ValidationError):
            route_order_to_execution_node(self.client_user, self.broker_details, {"symbol": "NIFTY", "quantity": 1})

    def test_hmac_signature_generation_and_verification(self):
        payload = {"hello": "world"}
        timestamp = str(int(timezone.now().timestamp()))
        signature = generate_node_signature("secret", timestamp, payload)
        verify_node_signature("secret", timestamp, payload, signature)
        with self.assertRaises(PermissionDenied):
            verify_node_signature("secret", timestamp, payload, "bad")

    def test_replay_timestamp_rejected(self):
        payload = {"hello": "world"}
        timestamp = "1"
        signature = generate_node_signature("secret", timestamp, payload)
        with self.assertRaises(PermissionDenied):
            verify_node_signature("secret", timestamp, payload, signature)

    @mock.patch("main.services.execution_router.requests.post")
    def test_successful_mocked_order_routing(self, mock_post):
        assign_execution_node_to_client(self.client_user, self.node)
        self.broker_details.refresh_from_db()
        mock_post.return_value = SimpleNamespace(
            ok=True,
            status_code=200,
            content=b"{}",
            json=lambda: {"status": "placed", "broker_response": {"status": "success", "order_id": "1"}},
        )
        result = route_order_to_execution_node(
            self.client_user,
            self.broker_details,
            {"symbol": "NIFTY", "quantity": 65, "transaction_type": "BUY", "idempotency_key": "route-1"},
        )
        self.assertEqual(result["status"], ExecutionOrderJob.STATUS_PLACED)
        self.assertTrue(ExecutionOrderJob.objects.filter(idempotency_key="route-1").exists())

    @mock.patch("main.services.execution_router.requests.post", side_effect=TimeoutError("timeout"))
    def test_failed_node_timeout_handling(self, mock_post):
        import requests

        mock_post.side_effect = requests.Timeout("timeout")
        assign_execution_node_to_client(self.client_user, self.node)
        self.broker_details.refresh_from_db()
        result = route_order_to_execution_node(
            self.client_user,
            self.broker_details,
            {"symbol": "NIFTY", "quantity": 65, "transaction_type": "BUY", "idempotency_key": "route-timeout"},
        )
        self.assertEqual(result["status"], "failed")

    def test_broker_adapter_selection(self):
        adapter = get_broker_adapter(self.broker_details)
        self.assertEqual(adapter.broker_name, "angel one")

    def test_all_supported_brokers_have_execution_node_adapters(self):
        broker_names = {
            "Upstox": "upstox",
            "Zerodha": "zerodha",
            "Alice Blue": "alice blue",
            "5Paisa": "5paisa",
            "FYERS": "fyers",
            "Dhan": "dhan",
        }
        for display_name, expected_name in broker_names.items():
            with self.subTest(display_name=display_name):
                broker = Broker.objects.create(broker_name=display_name, is_active=True)
                broker_details = ClientBrokerdetails.objects.create(
                    client=self.client_user,
                    broker_name=broker,
                    broker_API_KEY="api-key",
                    broker_API_UID="uid",
                    access_token="access-token",
                )
                adapter = get_broker_adapter(broker_details)
                self.assertEqual(adapter.broker_name, expected_name)

    def test_node_idempotency_duplicate_rejection(self):
        payload = {"broker_details_id": self.broker_details.id, "order": {"symbol": "NIFTY"}}
        timestamp = str(int(timezone.now().timestamp()))
        signature = generate_node_signature("node-secret", timestamp, payload)
        headers = {
            "HTTP_X_ALGOVIEW_NODE_ID": "node-1",
            "HTTP_X_ALGOVIEW_TIMESTAMP": timestamp,
            "HTTP_X_ALGOVIEW_SIGNATURE": signature,
            "HTTP_X_ALGOVIEW_IDEMPOTENCY_KEY": "dup-1",
        }
        with mock.patch("main.execution_node_views.get_broker_adapter") as adapter_factory:
            adapter_factory.return_value.validate_credentials.return_value = {"status": "success"}
            adapter_factory.return_value.place_order.return_value = {"status": "success"}
            first = self.client.post("/api/node/place-order/", data=payload, content_type="application/json", **headers)
            second = self.client.post("/api/node/place-order/", data=payload, content_type="application/json", **headers)
        self.assertEqual(first.status_code, 200)
        self.assertEqual(second.status_code, 409)
