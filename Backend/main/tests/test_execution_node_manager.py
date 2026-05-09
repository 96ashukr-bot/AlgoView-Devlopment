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
from main.services.proxy_utils import build_requests_proxy_config, mask_proxy_url, verify_proxy_public_ip
from main.fyersapi import place_fyers_orders
from main.upstock import place_upstox_orders
from main.fivepaisa import place_5paisa_order
from main.dhanapi import place_dhan_orders
from main.zerodha import place_zerodha_orders


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

    @mock.patch("main.brokers.angelone.place_angel_one_order")
    def test_angel_one_adapter_supports_proxy_and_passes_config(self, mock_place_order):
        adapter = get_broker_adapter(self.broker_details)
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_place_order.return_value = {"status": "success", "order_id": "angel-proxy-1"}
        self.assertTrue(adapter.supports_proxy)
        adapter.place_order(
            {
                "symbol": "NIFTY",
                "strike": "24400",
                "option_type": "CE",
                "quantity": 65,
                "transaction_type": "BUY",
            },
            proxy_config=proxy_config,
        )
        self.assertEqual(mock_place_order.call_args.kwargs["proxy_config"], proxy_config)

    @mock.patch("main.brokers.aliceblue.place_alice_orders")
    def test_alice_blue_adapter_supports_proxy_and_passes_config(self, mock_place_order):
        broker = Broker.objects.create(broker_name="Alice Blue", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=broker,
            broker_API_KEY="alice-api",
            broker_API_UID="alice-user",
        )
        adapter = get_broker_adapter(broker_details)
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_place_order.return_value = {"data": {"status": "completed", "order_id": "alice-proxy-1"}}
        self.assertTrue(adapter.supports_proxy)
        adapter.place_order(
            {
                "symbol": "NIFTY24400CE",
                "quantity": 65,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "Exchange": "NFO",
            },
            proxy_config=proxy_config,
        )
        self.assertEqual(mock_place_order.call_args.kwargs["proxy_config"], proxy_config)

    @mock.patch("main.Alice_Blue_Api.requests.get")
    def test_alice_blue_proxy_client_passes_proxies_to_requests(self, mock_get):
        from main.Alice_Blue_Api import ProxyAwareAliceblue

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_get.return_value = SimpleNamespace(status_code=200, text='{"stat":"Ok"}', reason="OK")
        alice = ProxyAwareAliceblue(user_id="alice-user", api_key="alice-api", proxy_config=proxy_config)
        alice._sub_urls["test"] = "test"
        alice._get("test")
        self.assertEqual(mock_get.call_args.kwargs["proxies"], proxy_config)

    @mock.patch("main.angelone.managers.session_manager.SmartConnect")
    def test_angel_one_session_builds_smart_connect_with_proxy(self, mock_smart_connect):
        from main.angelone.managers.session_manager import ClientSession

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        session = ClientSession(
            client_id="A1",
            api_key="api-key",
            session_key="session-key",
            access_token="access-token",
            proxy_config=proxy_config,
        )
        session.attach_smart_connect()
        mock_smart_connect.assert_called_once_with(api_key="api-key", proxies=proxy_config)

    @mock.patch("main.brokers.zerodha.place_zerodha_orders")
    def test_zerodha_adapter_supports_proxy_and_passes_config(self, mock_place_order):
        broker = Broker.objects.create(broker_name="Zerodha", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=broker,
            broker_API_KEY="kite-api",
            access_token="kite-access",
        )
        adapter = get_broker_adapter(broker_details)
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_place_order.return_value = {"data": {"status": "complete", "order_id": "kite-proxy-1"}}
        self.assertTrue(adapter.supports_proxy)
        adapter.place_order(
            {
                "symbol": "NIFTY",
                "strike": "24400",
                "option_type": "CE",
                "quantity": 65,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "Exchange": "NFO",
            },
            proxy_config=proxy_config,
        )
        self.assertEqual(mock_place_order.call_args.kwargs["proxy_config"], proxy_config)

    @mock.patch("main.zerodha.KiteConnect")
    def test_zerodha_order_client_receives_proxy_config(self, mock_kite_class):
        from main.zerodha import place_zerodha_orders

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        kite = mock_kite_class.return_value
        kite.VARIETY_REGULAR = "regular"
        kite.profile.return_value = {"user_id": "kite-user"}
        kite.instruments.return_value = [{"tradingsymbol": "NIFTY24400CE"}]
        kite.ltp.return_value = {"NFO:NIFTY24400CE": {"last_price": 10}}
        kite.place_order.return_value = "kite-order-1"
        kite.order_history.return_value = [{"status": "COMPLETE", "transaction_type": "BUY", "average_price": 10, "filled_quantity": 65}]
        place_zerodha_orders(
            10,
            "Lite",
            "kite-access",
            "kite-api",
            "NIFTY24400CE",
            "BUY",
            "NIFTY",
            65,
            "strategy",
            "LIMIT",
            "MIS",
            10,
            self.client_user,
            1,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "NFO",
            "FNO",
            "NIFTY",
            None,
            "OPEN",
            "kite-history-1",
            proxy_config=proxy_config,
        )
        mock_kite_class.assert_called_once_with(api_key="kite-api", proxies=proxy_config)

    @mock.patch("main.brokers.dhan.place_dhan_orders")
    def test_dhan_adapter_supports_proxy_and_passes_config(self, mock_place_order):
        broker = Broker.objects.create(broker_name="Dhan", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=broker,
            broker_API_UID="dhan-client",
            access_token="dhan-access",
        )
        adapter = get_broker_adapter(broker_details)
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_place_order.return_value = {"data": {"status": "completed", "order_id": "dhan-proxy-1"}}
        self.assertTrue(adapter.supports_proxy)
        adapter.place_order(
            {
                "symbol": "NIFTY",
                "strike": "24400",
                "option_type": "CE",
                "quantity": 65,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "Exchange": "NFO",
            },
            proxy_config=proxy_config,
        )
        self.assertEqual(mock_place_order.call_args.kwargs["proxy_config"], proxy_config)

    @mock.patch("main.dhanapi.get_trading_symbol_security_id")
    @mock.patch("main.dhanapi.dhanhq")
    def test_dhan_order_client_receives_proxy_config(self, mock_dhan_class, mock_security_lookup):
        from main.dhanapi import place_dhan_orders

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        dhan = mock_dhan_class.return_value
        dhan.session.proxies = {}
        dhan.NSE_FNO = "NSE_FNO"
        dhan.NSE = "NSE"
        dhan.NORMAL = "NORMAL"
        dhan.INTRA = "INTRA"
        dhan.CNC = "CNC"
        dhan.BUY = "BUY"
        dhan.SELL = "SELL"
        dhan.MARKET = "MARKET"
        dhan.LIMIT = "LIMIT"
        dhan.SL = "SL"
        dhan.get_ltp_data.return_value = {"data": {"NSE_FNO": {"12345": {"last_price": 10}}}}
        dhan.place_order.return_value = {"status": "success", "data": {"orderId": "dhan-order-1"}}
        dhan.get_order_by_id.return_value = {
            "status": "success",
            "data": [{"orderStatus": "TRADED", "transactionType": "BUY", "averageTradedPrice": 10, "quantity": 65}],
        }
        mock_security_lookup.return_value = {"status": "success", "SECURITY_ID": 12345}
        place_dhan_orders(
            "2026-05-12",
            10,
            "Lite",
            "dhan-access",
            "dhan-client",
            "NIFTY24400CE",
            "BUY",
            "NIFTY",
            65,
            "strategy",
            "LIMIT",
            "MIS",
            10,
            self.client_user,
            1,
            None,
            None,
            None,
            None,
            None,
            None,
            None,
            "NFO",
            "FNO",
            "NIFTY",
            None,
            "OPEN",
            "dhan-history-1",
            proxy_config=proxy_config,
        )
        self.assertEqual(dhan.session.proxies, proxy_config)

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

    def test_proxy_node_without_vps_fields_succeeds(self):
        node = ExecutionNode.objects.create(
            name="Proxy Node",
            ip_address="10.0.0.20",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            provider="proxy-vendor",
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
        )
        node.set_proxy_password("secret")
        node.full_clean()
        self.assertEqual(node.get_proxy_password(), "secret")

    def test_proxy_node_requires_proxy_fields(self):
        node = ExecutionNode(name="Bad Proxy", ip_address="10.0.0.21", execution_type=ExecutionNode.EXECUTION_TYPE_PROXY)
        with self.assertRaises(ValidationError):
            node.full_clean()

    def test_proxy_config_masks_password(self):
        node = ExecutionNode(
            name="Proxy Node",
            ip_address="10.0.0.22",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=1080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_SOCKS5,
            proxy_username="user name",
        )
        node.set_proxy_password("p@ss word")
        config = build_requests_proxy_config(node)
        self.assertIn("socks5://user%20name:p%40ss%20word@proxy.example.com:1080", config["https"])
        self.assertNotIn("p@ss word", mask_proxy_url(node))

    def test_proxy_config_formats_ipv6_proxy_host(self):
        node = ExecutionNode(
            name="IPv6 Proxy Node",
            ip_address="2001:db8::10",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="2001:db8::20",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_username="ipv6 user",
        )
        node.set_proxy_password("ipv6 pass")
        config = build_requests_proxy_config(node)
        self.assertEqual(
            config["https"],
            "http://ipv6%20user:ipv6%20pass@[2001:db8::20]:8080",
        )

    def test_proxy_config_accepts_bracketed_ipv6_proxy_host(self):
        node = ExecutionNode(
            name="Bracketed IPv6 Proxy Node",
            ip_address="2001:db8::11",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="[2001:db8::21]",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTPS,
        )
        config = build_requests_proxy_config(node)
        self.assertEqual(config["https"], "https://[2001:db8::21]:8080")

    @mock.patch("main.services.proxy_utils.requests.get")
    def test_verify_proxy_public_ip_success(self, mock_get):
        node = ExecutionNode.objects.create(
            name="Proxy Verify",
            ip_address="10.0.0.23",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
        )
        mock_get.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {"ip": "10.0.0.23"},
            text="10.0.0.23",
            raise_for_status=lambda: None,
        )
        result = verify_proxy_public_ip(node)
        node.refresh_from_db()
        self.assertEqual(result["status"], "success")
        self.assertTrue(node.proxy_public_ip_verified)

    @mock.patch("main.services.proxy_utils.requests.get")
    def test_verify_proxy_public_ipv6_success_with_normalization(self, mock_get):
        node = ExecutionNode.objects.create(
            name="IPv6 Proxy Verify",
            ip_address="2001:db8::23",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="2001:db8::24",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
        )
        mock_get.return_value = SimpleNamespace(
            status_code=200,
            json=lambda: {"ip": "2001:0db8:0000:0000:0000:0000:0000:0023"},
            text="2001:0db8:0000:0000:0000:0000:0000:0023",
            raise_for_status=lambda: None,
        )
        result = verify_proxy_public_ip(node)
        node.refresh_from_db()
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["actual_ip"], "2001:db8::23")
        self.assertTrue(node.proxy_public_ip_verified)
        self.assertEqual(str(node.proxy_last_seen_ip), "2001:db8::23")

    @mock.patch("main.services.execution_router.get_broker_adapter")
    def test_proxy_order_routes_through_adapter(self, adapter_factory):
        proxy_node = ExecutionNode.objects.create(
            name="Proxy Route",
            ip_address="10.0.0.24",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=True,
        )
        assign_execution_node_to_client(self.client_user, proxy_node)
        self.broker_details.execution_node = proxy_node
        self.broker_details.save(update_fields=["execution_node"])
        adapter = adapter_factory.return_value
        adapter.supports_proxy = True
        adapter.validate_credentials.return_value = {"status": "success"}
        adapter.place_order.return_value = {"status": "success", "order_id": "proxy-1"}
        result = route_order_to_execution_node(
            self.client_user,
            self.broker_details,
            {"symbol": "NIFTY", "quantity": 1, "idempotency_key": "proxy-route-1"},
        )
        self.assertEqual(result["status"], ExecutionOrderJob.STATUS_PLACED)
        adapter.place_order.assert_called_once()
        self.assertIn("https", adapter.place_order.call_args.kwargs["proxy_config"])

    @mock.patch("main.services.execution_router.get_broker_adapter")
    def test_proxy_order_blocks_unsupported_adapter(self, adapter_factory):
        proxy_node = ExecutionNode.objects.create(
            name="Proxy Unsupported",
            ip_address="10.0.0.25",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=True,
        )
        assign_execution_node_to_client(self.client_user, proxy_node)
        self.broker_details.execution_node = proxy_node
        self.broker_details.save(update_fields=["execution_node"])
        adapter_factory.return_value.supports_proxy = False
        with self.assertRaises(ValidationError):
            route_order_to_execution_node(
                self.client_user,
                self.broker_details,
                {"symbol": "NIFTY", "quantity": 1, "idempotency_key": "proxy-route-unsupported"},
            )

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

    def test_direct_order_helpers_fail_closed_without_proxy(self):
        common = dict(
            LivePrice=None,
            group_service=None,
            transaction_type="BUY",
            symbol="NIFTY",
            quantity=1,
            strategy="test",
            ordertype="LIMIT",
            product_type="INTRADAY",
            price=1,
            user=self.client_user,
            Lots=1,
            Entry_type=None,
            Exit_type=None,
            Entry_price=None,
            Exit_price=None,
            EntryQty=None,
            ExitQty=None,
            webhook_signal=None,
            Exchange="NFO",
            Segment="FNO",
            Index_Symbol="NIFTY",
            triggerPrice=None,
            trade_order_status=None,
            history_id="no-proxy",
        )
        self.assertIn("Proxy/static-IP", place_fyers_orders(access_token="t", Api_key="k", trade_symbol="NIFTY", **common)["data"]["message"])
        self.assertIn("Proxy/static-IP", place_upstox_orders(access_token="t", trade_symbol="NIFTY", **common)["data"]["message"])
        self.assertIn("Proxy/static-IP", place_dhan_orders(expiry_date="2026-05-12", access_token="t", client_id="c", trade_symbol="NIFTY", **common)["data"]["message"])
        self.assertIn("Proxy/static-IP", place_zerodha_orders(access_token="t", Api_key="k", trade_symbol="NIFTY", **common)["data"]["message"])
        self.assertIn(
            "Proxy/static-IP",
            place_5paisa_order(api_key="k", access_token="t", trade_symbol="NIFTY", trade=SimpleNamespace(), **common)["data"]["message"],
        )
