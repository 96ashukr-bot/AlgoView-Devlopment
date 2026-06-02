import os
import tempfile
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

import requests
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from main.brokers.base import get_broker_adapter
from main.models import Broker, ChatMessage, ChatThread, ClientBrokerdetails, ClientTradeSetting, ExecutionNode, ExecutionOrderJob, Role, Tradeorderhistory, User
from main.services.execution_nodes import assign_execution_node_to_client, release_execution_node
from main.services.execution_router import route_order_to_execution_node
from main.services.egress_guard import _is_broker_url, _is_public_instrument_master_url
from main.services.node_security import generate_node_signature, verify_node_signature
from main.services.proxy_utils import build_requests_proxy_config, mask_proxy_url, verify_proxy_public_ip
from main.fyersapi import place_fyers_orders
from main.upstock import place_upstox_orders
from main.fivepaisa import place_5paisa_order
from main.dhanapi import place_dhan_orders
from main.dhanapi import get_trading_symbol_security_id
from main.groww import generate_groww_access_token, generate_groww_checksum, place_groww_orders, resolve_groww_trading_symbol
from main.zerodha import place_zerodha_orders
from main.Alice_Blue_Api import place_alice_orders
from main.dematemodule import LEGACY_OPEN_BUY_ORDER_STATUSES, _broker_proxy_config_or_none, _legacy_exit_completed, _save_session_tokens_compat
from main.dematemodule import BrokerCallbackView, BrokerLoginRedirectView
from main.broker_registry import get_broker_setup_spec
from main.broker_order_utils import extract_ltp_from_quote_payload
from main.brokers.exchange_mapping import normalize_broker_exchange, normalize_fivepaisa_exchange
from main.brokers.utils import build_trade_symbol
from main.brokers.position_guard import find_matching_open_buy_position, mark_open_position_closed, prepare_close_order_from_open_position
from main.permissions import can_access_client_record
from main.services.live_price_cache import build_live_price_payload, cache_live_price, get_live_price
from main.services.option_ltp_fallback import cache_option_ltp, fetch_nse_option_chain_ltp, get_cached_option_ltp
from main.sl_tp_watcher_service import SLTPWatcherService, SUCCESS_EXIT_STATUSES
from main.services.upstox_market_data import UpstoxInstrumentResolver, get_active_option_instruments
from main.serializers import ClientBrokerDetailsUpdateSerializer, TradeorderhistorySerializer
from main.trade_history_service import save_trade_order_history
from main.views import _process_webhook_trade, _resolve_webhook_request_context, place_order_broker


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

    def test_sensex_exchange_mapping_is_broker_specific(self):
        self.assertEqual(normalize_broker_exchange("Angel One", "BSE", "SENSEX"), "BFO")
        self.assertEqual(normalize_broker_exchange("Alice Blue", "BSE", "SENSEX"), "BFO")
        self.assertEqual(normalize_broker_exchange("Zerodha", "BSE", "SENSEX"), "BFO")
        self.assertEqual(normalize_broker_exchange("Dhan", "BSE", "SENSEX"), "BSE_FNO")
        self.assertEqual(normalize_broker_exchange("Fyers", "BSE", "SENSEX"), "BSE_FO")
        self.assertEqual(normalize_broker_exchange("Upstox", "BSE", "SENSEX"), "BSE")
        self.assertEqual(normalize_fivepaisa_exchange("BSE", "SENSEX"), ("bse_fo", "B"))

    def test_nse_index_exchange_mapping_stays_unchanged(self):
        for underlying in ("NIFTY", "BANKNIFTY", "FINNIFTY"):
            self.assertEqual(normalize_broker_exchange("Angel One", "NFO", underlying), "NFO")
            self.assertEqual(normalize_broker_exchange("Dhan", "NFO", underlying), "NFO")
            self.assertEqual(normalize_broker_exchange("Fyers", "NFO", underlying), "NFO")
            self.assertEqual(normalize_fivepaisa_exchange("NFO", underlying), ("nse_fo", "N"))

    @mock.patch("main.brokers.angelone.place_angel_one_order")
    def test_angel_one_adapter_maps_sensex_to_bfo(self, mock_place_order):
        mock_place_order.return_value = {"data": {"status": "completed", "order_id": "angel-sensex-1"}}
        adapter = get_broker_adapter(self.broker_details)
        adapter.place_order(
            {
                "symbol": "SENSEX",
                "strike": "80000",
                "option_type": "CE",
                "quantity": 20,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "Exchange": "BSE",
            }
        )
        self.assertEqual(mock_place_order.call_args.kwargs["exchange"], "BFO")

    @mock.patch("main.brokers.angelone.place_angel_one_order")
    def test_angel_one_adapter_keeps_nifty_on_nfo(self, mock_place_order):
        mock_place_order.return_value = {"data": {"status": "completed", "order_id": "angel-nifty-1"}}
        adapter = get_broker_adapter(self.broker_details)
        adapter.place_order(
            {
                "symbol": "NIFTY",
                "strike": "24400",
                "option_type": "CE",
                "quantity": 75,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "Exchange": "NFO",
            }
        )
        self.assertEqual(mock_place_order.call_args.kwargs["exchange"], "NFO")

    def test_superadmin_trade_history_includes_all_clients_and_failed_rows(self):
        superadmin = User.objects.create_user(
            email="trade-superadmin@example.com",
            firstName="Trade",
            lastName="Super",
            phoneNumber="9999999901",
            password="Pass@123",
            is_superuser=True,
        )
        assigned_client = User.objects.create_user(
            email="assigned-history@example.com",
            firstName="Assigned",
            lastName="History",
            phoneNumber="9999999902",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
        )
        unassigned_client = User.objects.create_user(
            email="unassigned-history@example.com",
            firstName="Unassigned",
            lastName="History",
            phoneNumber="9999999903",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
        )
        Tradeorderhistory.objects.create(
            client=assigned_client,
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY",
            order_id="order-1",
            order_status="completed",
        )
        Tradeorderhistory.objects.create(
            client=unassigned_client,
            trading_symbol="BANKNIFTY",
            Index_Symbol="BANKNIFTY",
            order_id=None,
            order_status="Failed",
            response_data={"data": {"status": "Failed", "message": "Insufficient margin"}},
        )

        access_token = str(RefreshToken.for_user(superadmin).access_token)
        response = self.client.get(
            "/api/get-trade-history/",
            {"page_size": 50},
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        emails = {item["client"]["email"] for item in response.data["results"]}
        self.assertIn("assigned-history@example.com", emails)
        self.assertIn("unassigned-history@example.com", emails)
        failed_trade = next(
            item for item in response.data["results"] if item["client"]["email"] == "unassigned-history@example.com"
        )
        self.assertEqual(failed_trade["failure_reason"], "Insufficient margin")
        self.assertEqual(failed_trade["broker_response"], "Insufficient margin")

    def test_successful_trade_history_suppresses_internal_routing_failure_reason(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY26MAY2624000CE",
            order_status="open",
            trade_order_status="OPEN",
            failure_reason="Order routed to execution node.",
            response_data={"data": {"status": "open", "message": "Order routed to execution node."}},
        )

        data = TradeorderhistorySerializer(history).data

        self.assertIsNone(data["failure_reason"])
        self.assertEqual(data["broker_response"], "Order routed to execution node.")

    def test_successful_trade_history_includes_broker_response_message(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY26MAY2624000CE",
            order_status="complete",
            trade_order_status="OPEN",
            response_data={"data": {"status": "success", "message": "Order placed successfully"}},
        )

        data = TradeorderhistorySerializer(history).data

        self.assertIsNone(data["failure_reason"])
        self.assertEqual(data["broker_response"], "Order placed successfully")

    def test_trade_history_placeholder_is_not_saved_as_failure_reason(self):
        save_trade_order_history(
            100,
            "test",
            "BUY",
            "ENTRY",
            self.client_user,
            None,
            0,
            "Failed",
            "Order is placing by place order broker !!",
            "Order is placing by place order broker !!",
            "test-strategy",
            "BUY",
            None,
            None,
            None,
            75,
            None,
            {},
            "NFO",
            "OPT",
            "NIFTY",
            {"quantity": 75},
            history_id="placeholder-history",
        )

        history = Tradeorderhistory.objects.get(history_id="placeholder-history")

        self.assertIsNone(history.failure_reason)

    def test_trade_history_success_update_clears_old_failure_reason(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="clear-failure-history",
            trading_symbol="NIFTY26MAY2624000CE",
            order_status="Failed",
            trade_order_status="Failed",
            failure_reason="Old failure",
        )

        save_trade_order_history(
            100,
            "test",
            "BUY",
            "OPEN",
            self.client_user,
            "NIFTY26MAY2624000CE",
            "order-1",
            "open",
            {"data": {"status": "open", "message": "Success", "order_id": "order-1"}},
            "Success",
            "test",
            None,
            None,
            None,
            None,
            65,
            None,
            {},
            "NFO",
            "FNO",
            "NIFTY26MAY2624000CE",
            {},
            broker="Alice Blue",
            history_id=history.history_id,
        )

        history.refresh_from_db()
        self.assertIsNone(history.failure_reason)
        self.assertEqual(history.order_status, "open")

    @mock.patch("main.views.get_execution_engine")
    def test_place_order_broker_overwrites_placeholder_with_engine_failure(self, mock_get_engine):
        mock_get_engine.return_value.execute_order.return_value = {
            "data": {
                "status": "Failed",
                "message": "No valid Angel One session is available. Please complete broker login again.",
                "error_code": "TOKEN_EXPIRED",
            }
        }
        trade = SimpleNamespace(broker="Angel One")

        place_order_broker(
            100,
            "test",
            trade,
            self.client_user,
            "SELL",
            "NIFTY",
            65,
            "test-strategy",
            "LIMIT",
            "MIS",
            None,
            1,
            None,
            None,
            None,
            None,
            None,
            None,
            65,
            {"ordertype": "buy-C"},
            "NFO",
            "FNO",
            "NIFTY",
            None,
            "02",
            "JUN",
            "26",
            "2026",
            23300,
            "PE",
            {"transaction_type": "SELL", "option_type": "PE", "quantity": 65},
            "engine-failure-history",
        )

        history = Tradeorderhistory.objects.get(history_id="engine-failure-history")
        self.assertEqual(history.failure_reason, "No valid Angel One session is available. Please complete broker login again.")
        self.assertEqual(history.response_data["data"]["error_code"], "TOKEN_EXPIRED")
        self.assertEqual(history.broker, "Angel One")

    def test_subadmin_trade_history_is_limited_to_assigned_clients(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        subadmin = User.objects.create_user(
            email="trade-subadmin@example.com",
            firstName="Trade",
            lastName="Sub",
            phoneNumber="9999999904",
            password="Pass@123",
            role=subadmin_role,
        )
        assigned_client = User.objects.create_user(
            email="sub-assigned-history@example.com",
            firstName="Sub",
            lastName="Assigned",
            phoneNumber="9999999905",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
            assigned_client=subadmin,
        )
        other_client = User.objects.create_user(
            email="sub-other-history@example.com",
            firstName="Sub",
            lastName="Other",
            phoneNumber="9999999906",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
        )
        Tradeorderhistory.objects.create(
            client=assigned_client,
            trading_symbol="NIFTY",
            order_id=None,
            order_status="Failed",
            response_data={"data": {"status": "Failed", "skip_reasons": ["Broker access token is missing"]}},
        )
        Tradeorderhistory.objects.create(client=other_client, trading_symbol="BANKNIFTY", order_status="completed")

        access_token = str(RefreshToken.for_user(subadmin).access_token)
        response = self.client.get(
            "/api/get-trade-history/",
            {"page_size": 50},
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        emails = {item["client"]["email"] for item in response.data["results"]}
        self.assertIn("sub-assigned-history@example.com", emails)
        self.assertNotIn("sub-other-history@example.com", emails)
        assigned_trade = next(
            item for item in response.data["results"] if item["client"]["email"] == "sub-assigned-history@example.com"
        )
        self.assertEqual(assigned_trade["failure_reason"], "Broker access token is missing")

    def test_client_trade_history_is_limited_to_self(self):
        self_client = User.objects.create_user(
            email="self-history@example.com",
            firstName="Self",
            lastName="History",
            phoneNumber="9999999907",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
        )
        other_client = User.objects.create_user(
            email="other-history@example.com",
            firstName="Other",
            lastName="History",
            phoneNumber="9999999908",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
        )
        Tradeorderhistory.objects.create(client=self_client, trading_symbol="NIFTY", order_status="completed")
        Tradeorderhistory.objects.create(client=other_client, trading_symbol="BANKNIFTY", order_status="completed")

        access_token = str(RefreshToken.for_user(self_client).access_token)
        response = self.client.get(
            "/api/get-client-trade-history/",
            {"page_size": 50},
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        emails = {item["client"]["email"] for item in response.data["results"]}
        self.assertIn("self-history@example.com", emails)
        self.assertNotIn("other-history@example.com", emails)

    def test_client_access_check_handles_client_with_missing_email(self):
        superadmin = User.objects.create_user(
            email="delete-superadmin@example.com",
            firstName="Delete",
            lastName="Admin",
            phoneNumber="9999999910",
            password="Pass@123",
            is_superuser=True,
        )
        client = User.objects.create_user(
            email="subhash-delete@example.com",
            firstName="Subhash",
            lastName="Varlani",
            phoneNumber="9999999911",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
        )
        client.email = None
        client.save(update_fields=["email"])

        self.assertIsInstance(str(client), str)
        self.assertTrue(str(client))
        self.assertTrue(can_access_client_record(superadmin, client))

    def test_disabled_client_webhook_skip_does_not_reach_trade_history(self):
        disabled_client = User.objects.create_user(
            email="disabled-history@example.com",
            firstName="Disabled",
            lastName="History",
            phoneNumber="9999999909",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
            is_enable=False,
        )
        trade = ClientTradeSetting.objects.create(
            client=disabled_client,
            symbol="NIFTY",
            group_service="NIFTY",
            broker="Angel One",
            product_type="INTRADAY",
            quantity=1,
            trade_limit=10,
            is_tread_status=True,
        )
        context = {
            "alert_data": {"symbol": "NIFTY"},
            "symbols": "NIFTY",
            "exch_seg": "NFO",
            "default_price": 10,
            "default_quantity": 1,
            "live_price": 10,
            "lots": 1,
            "trigger_price": 0,
            "transaction_type": "BUY",
            "buy_sell": "CE",
            "limit_price": 10,
            "strategy_id": "NIFTY",
        }

        result = _process_webhook_trade(trade, 0, context, history_id="disabled-client-skip")

        self.assertEqual(result["status"], "skipped")
        self.assertFalse(result["recorded_in_trade_history"])
        self.assertIn("Client trading is disabled", result["skip_reasons"])
        self.assertFalse(Tradeorderhistory.objects.filter(client=disabled_client).exists())

    @mock.patch("main.views.place_order_broker")
    def test_expired_trade_expiry_skips_webhook_before_broker_execution(self, mock_place_order):
        trade = ClientTradeSetting.objects.create(
            client=self.client_user,
            symbol="NIFTY",
            group_service="NIFTY",
            broker="Angel One",
            product_type="INTRADAY",
            quantity=65,
            trade_limit=10,
            is_tread_status=True,
            expiry_date=timezone.now() - timezone.timedelta(days=1),
        )
        context = {
            "alert_data": {"symbol": "NIFTY"},
            "symbols": "NIFTY",
            "exch_seg": "NFO",
            "default_price": 23600,
            "default_quantity": 65,
            "live_price": 100,
            "lots": 1,
            "trigger_price": 0,
            "transaction_type": "BUY",
            "buy_sell": "CE",
            "limit_price": 100,
            "strategy_id": "NIFTY",
        }

        result = _process_webhook_trade(trade, 0, context, history_id="expired-expiry-skip")

        self.assertEqual(result["status"], "skipped")
        self.assertIn("Expiry date has expired. Please update expiry date.", result["skip_reasons"])
        mock_place_order.assert_not_called()
        history = Tradeorderhistory.objects.get(history_id="expired-expiry-skip")
        self.assertEqual(history.order_status, "Failed")
        self.assertIn("Expiry date has expired", history.failure_reason)

    def test_tradingview_webhook_language_decodes_expected_contracts(self):
        cases = {
            "BUY-O": ("CE", "Buy CE"),
            "SELL-C": ("CE", "Close CE"),
            "SELL-C_O": ("CE PE", "Close CE & Buy PE"),
            "SELL-O": ("PE", "BUY PE"),
            "BUY-C": ("PE", "Close PE"),
            "BUY-C_O": ("PE CE", "Close PE & Buy CE"),
        }

        for ordertype, (buy_sell, _description) in cases.items():
            context = _resolve_webhook_request_context(
                {
                    "text": "NIFTY FIN SERVICE",
                    "ordertype": ordertype,
                    "signalprice": "26115.60",
                    "stratergyid": "Sparks Lite",
                }
            )
            self.assertEqual(context["symbols"], "FINNIFTY")
            self.assertEqual(context["transaction_type"], ordertype)
            self.assertEqual(context["buy_sell"], buy_sell)

    @mock.patch("main.views.place_order_broker")
    def test_combined_sell_c_o_creates_distinct_close_ce_and_open_pe_legs(self, mock_place_order):
        mock_place_order.return_value = {"data": {"status": "complete", "message": "ok"}}
        self.broker_details.set_broker_password("trading-password")
        self.broker_details.set_broker_totp_secret("BASE32SECRET")
        self.broker_details.save()
        trade = ClientTradeSetting.objects.create(
            client=self.client_user,
            symbol="FINNIFTY",
            group_service="Sparks Lite",
            broker="Angel One",
            product_type="INTRADAY",
            quantity=60,
            trade_limit=10,
            is_tread_status=True,
            expiry_date=timezone.now(),
        )
        context = _resolve_webhook_request_context(
            {
                "text": "NIFTY FIN SERVICE",
                "ordertype": "SELL-C_O",
                "signalprice": "26115.60",
                "stratergyid": "Sparks Lite",
            }
        )

        _process_webhook_trade(trade, 0, context, history_id="combo-sell-c-o")

        self.assertEqual(mock_place_order.call_count, 2)
        close_call = mock_place_order.call_args_list[0].args
        open_call = mock_place_order.call_args_list[1].args
        self.assertEqual(close_call[4], "SELL")
        self.assertEqual(close_call[29], "CE")
        self.assertEqual(close_call[30]["transaction_type"], "SELL")
        self.assertEqual(close_call[30]["option_type"], "CE")
        self.assertEqual(close_call[31], "combo-sell-c-o_close_ce")
        self.assertEqual(open_call[4], "BUY")
        self.assertEqual(open_call[29], "PE")
        self.assertEqual(open_call[30]["transaction_type"], "BUY")
        self.assertEqual(open_call[30]["option_type"], "PE")
        self.assertEqual(open_call[31], "combo-sell-c-o_open_pe")

    @mock.patch("main.views.place_order_broker")
    def test_combined_buy_c_o_creates_distinct_close_pe_and_open_ce_legs(self, mock_place_order):
        mock_place_order.return_value = {"data": {"status": "complete", "message": "ok"}}
        self.broker_details.set_broker_password("trading-password")
        self.broker_details.set_broker_totp_secret("BASE32SECRET")
        self.broker_details.save()
        trade = ClientTradeSetting.objects.create(
            client=self.client_user,
            symbol="FINNIFTY",
            group_service="Sparks Lite",
            broker="Angel One",
            product_type="INTRADAY",
            quantity=60,
            trade_limit=10,
            is_tread_status=True,
            expiry_date=timezone.now(),
        )
        context = _resolve_webhook_request_context(
            {
                "text": "NIFTY FIN SERVICE",
                "ordertype": "BUY-C_O",
                "signalprice": "26115.60",
                "stratergyid": "Sparks Lite",
            }
        )

        _process_webhook_trade(trade, 0, context, history_id="combo-buy-c-o")

        self.assertEqual(mock_place_order.call_count, 2)
        close_call = mock_place_order.call_args_list[0].args
        open_call = mock_place_order.call_args_list[1].args
        self.assertEqual(close_call[4], "SELL")
        self.assertEqual(close_call[29], "PE")
        self.assertEqual(close_call[30]["transaction_type"], "SELL")
        self.assertEqual(close_call[30]["option_type"], "PE")
        self.assertEqual(close_call[31], "combo-buy-c-o_close_pe")
        self.assertEqual(open_call[4], "BUY")
        self.assertEqual(open_call[29], "CE")
        self.assertEqual(open_call[30]["transaction_type"], "BUY")
        self.assertEqual(open_call[30]["option_type"], "CE")
        self.assertEqual(open_call[31], "combo-buy-c-o_open_ce")

    def test_exit_position_matches_open_buy_when_index_symbol_is_full_contract(self):
        Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY26MAY2624000PE",
            Index_Symbol="NIFTY2624000PE26MAY",
            transaction_type="BUY",
            trade_order_status="complete",
            order_status="complete",
            order_id="260525000362199",
            Entry_type="BUY",
            EntryQty=65,
            Entry_Price=105,
            order_params={"transaction_type": "PE", "symbol": "NIFTY"},
        )

        match = find_matching_open_buy_position(
            self.client_user,
            {
                "symbol": "NIFTY",
                "group_service": "Lite",
                "transaction_type": "SELL",
                "option_type": "PE",
                "quantity": 65,
            },
        )

        self.assertIsNotNone(match)
        self.assertEqual(match.order_id, "260525000362199")

        close_order, open_position, close_error = prepare_close_order_from_open_position(
            self.client_user,
            {
                "symbol": "NIFTY",
                "group_service": "Lite",
                "transaction_type": "SELL",
                "option_type": "PE",
                "quantity": 65,
            },
            "angel one",
        )
        self.assertIsNone(close_error)
        self.assertEqual(open_position.order_id, "260525000362199")
        self.assertEqual(close_order["strike"], "24000")
        self.assertEqual(close_order["option_type"], "PE")
        self.assertEqual(close_order["quantity"], 65)

    def test_exit_uses_existing_open_buy_contract_when_signal_reference_price_changes(self):
        Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY26MAY2624000CE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="complete",
            order_status="complete",
            order_id="nifty-ce-open",
            Entry_type="BUY",
            EntryQty=65,
            Entry_Price=110,
            LivePrice=24049,
            webhook_signal={"ordertype": "BUY-O", "price": 24049},
            order_params={"transaction_type": "CE", "symbol": "NIFTY", "strike": 24000},
        )

        close_order, open_position, close_error = prepare_close_order_from_open_position(
            self.client_user,
            {
                "symbol": "NIFTY",
                "group_service": "Lite",
                "transaction_type": "SELL",
                "option_type": "CE",
                "quantity": 65,
                "strike": 24100,
                "LivePrice": 24085,
                "webhook_signal": {"ordertype": "SELL-C", "price": 24085},
            },
            "angel one",
        )

        self.assertIsNone(close_error)
        self.assertEqual(open_position.order_id, "nifty-ce-open")
        self.assertEqual(close_order["strike"], "24000")
        self.assertEqual(close_order["option_type"], "CE")
        self.assertEqual(close_order["quantity"], 65)

    def test_exit_matches_broker_accepted_open_buy_order(self):
        Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="open",
            order_status="open",
            order_id="26060100028066",
            Entry_type="BUY",
            EntryQty=65,
            Entry_Price=137.05,
            response_data={
                "data": {
                    "status": "open",
                    "message": "Success",
                    "order_id": "26060100028066",
                    "response": {
                        "status": "Ok",
                        "message": "Success",
                    },
                }
            },
            order_params={
                "transaction_type": "BUY",
                "option_type": "CE",
                "symbol": "NIFTY",
                "strike": 23600,
            },
        )

        close_order, open_position, close_error = prepare_close_order_from_open_position(
            self.client_user,
            {
                "symbol": "NIFTY",
                "transaction_type": "SELL",
                "option_type": "CE",
                "quantity": 65,
                "strike": 23600,
            },
            "alice blue",
        )

        self.assertIsNone(close_error)
        self.assertEqual(open_position.order_id, "26060100028066")
        self.assertEqual(str(close_order["strike"]), "23600")
        self.assertEqual(close_order["option_type"], "CE")
        self.assertEqual(close_order["quantity"], 65)

    def test_routed_open_exit_does_not_close_buy_position(self):
        buy_history = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY02JUN2623500CE",
            Index_Symbol="NIFTY02JUN2623500CE",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="completed",
            order_id="buy-open-1",
            Entry_type="LE",
            EntryQty=65,
        )

        mark_open_position_closed(
            buy_history,
            {"data": {"status": "open", "message": "Order routed to execution node."}},
        )

        buy_history.refresh_from_db()
        self.assertEqual(buy_history.trade_order_status, "OPEN")

    def test_completed_exit_closes_buy_position(self):
        buy_history = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY02JUN2623500CE",
            Index_Symbol="NIFTY02JUN2623500CE",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="completed",
            order_id="buy-completed-1",
            Entry_type="LE",
            EntryQty=65,
        )

        mark_open_position_closed(
            buy_history,
            {"data": {"status": "completed", "message": "Order completed successfully."}},
        )

        buy_history.refresh_from_db()
        self.assertEqual(buy_history.trade_order_status, "CLOSE")

    def test_sltp_watcher_does_not_treat_open_exit_as_success(self):
        self.assertNotIn("open", SUCCESS_EXIT_STATUSES)

    def test_legacy_exit_helpers_require_completed_status_to_close(self):
        for status_value in ("open", "pending", "transit", "rejected", "put order req received"):
            self.assertFalse(_legacy_exit_completed({"data": {"status": status_value}}))
        for status_value in ("complete", "completed", "success", "closed", "traded", "Fully Executed"):
            self.assertTrue(_legacy_exit_completed({"data": {"status": status_value}}))

    def test_legacy_open_buy_candidates_do_not_include_rejected_or_pending(self):
        self.assertNotIn("rejected", LEGACY_OPEN_BUY_ORDER_STATUSES)
        self.assertNotIn("pending", LEGACY_OPEN_BUY_ORDER_STATUSES)
        self.assertNotIn("transit", LEGACY_OPEN_BUY_ORDER_STATUSES)

    def test_exit_position_does_not_match_pending_open_buy_order(self):
        Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY26JUN23700CE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="OPEN",
            order_id="nifty-ce-pending-open",
            EntryQty=65,
            Entry_Price=203.95,
            order_params={"transaction_type": "BUY", "option_type": "CE", "symbol": "NIFTY", "strike": 23700},
        )

        close_order, open_position, close_error = prepare_close_order_from_open_position(
            self.client_user,
            {
                "symbol": "NIFTY",
                "group_service": "Lite",
                "transaction_type": "SELL",
                "option_type": "CE",
                "quantity": 65,
            },
            "zerodha",
        )

        self.assertIsNone(open_position)
        self.assertEqual(close_order["transaction_type"], "SELL")
        self.assertIn("No open BUY CE position", close_error["data"]["message"])

    def test_exit_position_does_not_match_banknifty_when_closing_nifty(self):
        Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="BANKNIFTY26MAY2654000PE",
            Index_Symbol="BANKNIFTY2654000PE26MAY",
            transaction_type="BUY",
            trade_order_status="complete",
            order_status="complete",
            order_id="banknifty-open",
            EntryQty=30,
            order_params={"transaction_type": "PE", "symbol": "BANKNIFTY"},
        )

        match = find_matching_open_buy_position(
            self.client_user,
            {
                "symbol": "NIFTY",
                "group_service": "Lite",
                "transaction_type": "SELL",
                "option_type": "PE",
                "quantity": 65,
            },
        )

        self.assertIsNone(match)

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
        broker_response = {"status": "success", "order_id": "1"}
        mock_post.return_value = SimpleNamespace(
            ok=True,
            status_code=200,
            content=b"{}",
            json=lambda: {"status": "placed", "broker_response": broker_response},
        )
        result = route_order_to_execution_node(
            self.client_user,
            self.broker_details,
            {
                "symbol": "NIFTY",
                "quantity": 65,
                "transaction_type": "BUY",
                "idempotency_key": "route-1",
                "Entry_price": Decimal("123.45"),
                "order_params": {"current_ltp": Decimal("120.50")},
            },
        )
        self.assertEqual(result["status"], ExecutionOrderJob.STATUS_PLACED)
        self.assertEqual(result["broker_response"], broker_response)
        self.assertTrue(ExecutionOrderJob.objects.filter(idempotency_key="route-1").exists())
        sent_payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(sent_payload["order"]["Entry_price"], 123.45)
        self.assertEqual(sent_payload["order"]["order_params"]["current_ltp"], 120.5)

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

    def test_subadmin_cannot_access_ip_pool_api(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        subadmin = User.objects.create_user(
            email="subadmin-ip-pool@example.com",
            firstName="Sub",
            lastName="Admin",
            phoneNumber="9999999997",
            password="Pass@123",
            role=subadmin_role,
        )
        access_token = str(RefreshToken.for_user(subadmin).access_token)

        response = self.client.get("/api/execution-nodes/", HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.assertEqual(response.status_code, 403)
        self.assertIn("Only superadmin users can manage the IP pool", str(response.json()))

    def test_superadmin_can_access_ip_pool_api(self):
        superadmin = User.objects.create_user(
            email="superadmin-ip-pool@example.com",
            firstName="Super",
            lastName="Admin",
            phoneNumber="9999999996",
            password="Pass@123",
            is_superuser=True,
        )
        access_token = str(RefreshToken.for_user(superadmin).access_token)

        response = self.client.get("/api/execution-nodes/", HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.assertEqual(response.status_code, 200)
        self.assertIn("results", response.json())

    def test_superadmin_can_delete_unassigned_ip_pool_node(self):
        superadmin = User.objects.create_user(
            email="superadmin-delete-ip-pool@example.com",
            firstName="Super",
            lastName="Admin",
            phoneNumber="9999999995",
            password="Pass@123",
            is_superuser=True,
        )
        access_token = str(RefreshToken.for_user(superadmin).access_token)

        response = self.client.delete(f"/api/execution-nodes/{self.node.id}/", HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.assertEqual(response.status_code, 204)
        self.assertFalse(ExecutionNode.objects.filter(id=self.node.id).exists())

    def test_superadmin_cannot_delete_assigned_ip_pool_node(self):
        assign_execution_node_to_client(self.client_user, self.node)
        superadmin = User.objects.create_user(
            email="superadmin-delete-assigned-ip-pool@example.com",
            firstName="Super",
            lastName="Admin",
            phoneNumber="9999999994",
            password="Pass@123",
            is_superuser=True,
        )
        access_token = str(RefreshToken.for_user(superadmin).access_token)

        response = self.client.delete(f"/api/execution-nodes/{self.node.id}/", HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.assertEqual(response.status_code, 400)
        self.assertTrue(ExecutionNode.objects.filter(id=self.node.id).exists())

    def test_client_can_create_support_chat_and_subadmin_can_reply(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        subadmin = User.objects.create_user(
            email="chat-subadmin@example.com",
            firstName="Chat",
            lastName="Subadmin",
            phoneNumber="9999999101",
            password="Pass@123",
            role=subadmin_role,
        )
        self.client_user.assigned_client = subadmin
        self.client_user.type_of_user = "is_client"
        self.client_user.is_client = "True"
        self.client_user.save(update_fields=["assigned_client", "type_of_user", "is_client"])

        client_token = str(RefreshToken.for_user(self.client_user).access_token)
        create_response = self.client.post(
            "/api/support-chat/threads/",
            {"subject": "Broker token", "message": "Please check my broker token."},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {client_token}",
        )
        self.assertEqual(create_response.status_code, 201)
        thread_id = create_response.data["id"]
        thread = ChatThread.objects.get(id=thread_id)
        self.assertEqual(thread.client_id, self.client_user.id)
        self.assertEqual(thread.assigned_subadmin_id, subadmin.id)

        subadmin_token = str(RefreshToken.for_user(subadmin).access_token)
        reply_response = self.client.post(
            f"/api/support-chat/threads/{thread_id}/messages/",
            {"message": "We are checking it."},
            format="json",
            HTTP_AUTHORIZATION=f"Bearer {subadmin_token}",
        )
        self.assertEqual(reply_response.status_code, 201)
        self.assertEqual(reply_response.data["sender_role"], ChatMessage.SENDER_SUBADMIN)

        detail_response = self.client.get(
            f"/api/support-chat/threads/{thread_id}/",
            HTTP_AUTHORIZATION=f"Bearer {client_token}",
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertEqual(len(detail_response.data["messages"]), 2)

    def test_support_chat_unread_count_clears_when_thread_is_opened(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        subadmin = User.objects.create_user(
            email="chat-badge-subadmin@example.com",
            firstName="Badge",
            lastName="Subadmin",
            phoneNumber="9999999105",
            password="Pass@123",
            role=subadmin_role,
        )
        self.client_user.assigned_client = subadmin
        self.client_user.type_of_user = "is_client"
        self.client_user.is_client = "True"
        self.client_user.save(update_fields=["assigned_client", "type_of_user", "is_client"])

        thread = ChatThread.objects.create(client=self.client_user, assigned_subadmin=subadmin, subject="Badge")
        ChatMessage.objects.create(
            thread=thread,
            sender=subadmin,
            sender_role=ChatMessage.SENDER_SUBADMIN,
            message="Please check this reply.",
            is_read_by_client=False,
            is_read_by_staff=True,
        )
        client_token = str(RefreshToken.for_user(self.client_user).access_token)

        unread_response = self.client.get(
            "/api/support-chat/unread-count/",
            HTTP_AUTHORIZATION=f"Bearer {client_token}",
        )
        self.assertEqual(unread_response.status_code, 200)
        self.assertEqual(unread_response.data["unread_count"], 1)
        self.assertEqual(unread_response.data["unread_thread_count"], 1)

        detail_response = self.client.get(
            f"/api/support-chat/threads/{thread.id}/",
            HTTP_AUTHORIZATION=f"Bearer {client_token}",
        )
        self.assertEqual(detail_response.status_code, 200)

        cleared_response = self.client.get(
            "/api/support-chat/unread-count/",
            HTTP_AUTHORIZATION=f"Bearer {client_token}",
        )
        self.assertEqual(cleared_response.status_code, 200)
        self.assertEqual(cleared_response.data["unread_count"], 0)

    def test_subadmin_cannot_view_unassigned_client_chat_but_superadmin_can(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        assigned_subadmin = User.objects.create_user(
            email="chat-assigned-subadmin@example.com",
            firstName="Assigned",
            lastName="Subadmin",
            phoneNumber="9999999102",
            password="Pass@123",
            role=subadmin_role,
        )
        other_subadmin = User.objects.create_user(
            email="chat-other-subadmin@example.com",
            firstName="Other",
            lastName="Subadmin",
            phoneNumber="9999999103",
            password="Pass@123",
            role=subadmin_role,
        )
        self.client_user.assigned_client = assigned_subadmin
        self.client_user.type_of_user = "is_client"
        self.client_user.is_client = "True"
        self.client_user.save(update_fields=["assigned_client", "type_of_user", "is_client"])
        thread = ChatThread.objects.create(client=self.client_user, assigned_subadmin=assigned_subadmin, subject="Access")
        ChatMessage.objects.create(thread=thread, sender=self.client_user, sender_role=ChatMessage.SENDER_CLIENT, message="Hello")

        other_token = str(RefreshToken.for_user(other_subadmin).access_token)
        denied_response = self.client.get(
            f"/api/support-chat/threads/{thread.id}/",
            HTTP_AUTHORIZATION=f"Bearer {other_token}",
        )
        self.assertEqual(denied_response.status_code, 404)

        superadmin = User.objects.create_user(
            email="chat-superadmin@example.com",
            firstName="Chat",
            lastName="Superadmin",
            phoneNumber="9999999104",
            password="Pass@123",
            is_superuser=True,
        )
        superadmin_token = str(RefreshToken.for_user(superadmin).access_token)
        allowed_response = self.client.get(
            f"/api/support-chat/threads/{thread.id}/",
            HTTP_AUTHORIZATION=f"Bearer {superadmin_token}",
        )
        self.assertEqual(allowed_response.status_code, 200)

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
                "day": "26",
                "month": "MAY",
                "fullyear": "2026",
            },
            proxy_config=proxy_config,
        )
        self.assertEqual(mock_place_order.call_args.kwargs["proxy_config"], proxy_config)
        self.assertEqual(mock_place_order.call_args.kwargs["expiry_override"].date().isoformat(), "2026-05-26")

    @mock.patch("main.brokers.dhan.place_dhan_orders")
    def test_dhan_adapter_maps_sensex_to_bse_fno(self, mock_place_order):
        broker = Broker.objects.create(broker_name="Dhan", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=broker,
            broker_API_UID="dhan-client",
            access_token="dhan-access",
        )
        adapter = get_broker_adapter(broker_details)
        mock_place_order.return_value = {"data": {"status": "completed", "order_id": "dhan-sensex-1"}}
        adapter.place_order(
            {
                "symbol": "SENSEX",
                "strike": "80000",
                "option_type": "CE",
                "quantity": 20,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "Exchange": "BSE",
            }
        )
        self.assertEqual(mock_place_order.call_args.args[22], "BSE_FNO")

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
                "trade_symbol": "NIFTY19MAY26C24400",
                "quantity": 65,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "Exchange": "NFO",
            },
            proxy_config=proxy_config,
        )
        self.assertEqual(mock_place_order.call_args.kwargs["proxy_config"], proxy_config)
        self.assertEqual(mock_place_order.call_args.args[22], "NFO")
        self.assertEqual(mock_place_order.call_args.args[4], "NIFTY19MAY26C24400")

    @mock.patch("main.brokers.aliceblue.place_alice_orders")
    def test_alice_blue_adapter_uses_saved_session_token_for_orders(self, mock_place_order):
        broker = Broker.objects.create(broker_name="Alice Blue", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=broker,
            broker_API_KEY="alice-api",
            broker_API_UID="alice-user",
            access_token="alice-session-token",
        )
        adapter = get_broker_adapter(broker_details)
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_place_order.return_value = {"data": {"status": "completed", "order_id": "alice-proxy-1"}}

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
        self.assertEqual(mock_place_order.call_args.kwargs["session_id"], "alice-session-token")

    @mock.patch("main.brokers.aliceblue.place_alice_orders")
    def test_alice_blue_adapter_builds_contract_symbol_when_trade_symbol_missing(self, mock_place_order):
        broker = Broker.objects.create(broker_name="Alice Blue", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=broker,
            broker_API_KEY="alice-api",
            broker_API_UID="alice-user",
            access_token="alice-session-token",
        )
        adapter = get_broker_adapter(broker_details)
        mock_place_order.return_value = {"data": {"status": "completed", "order_id": "alice-proxy-1"}}

        adapter.place_order(
            {
                "symbol": "NIFTY",
                "strike": 24400,
                "option_type": "CE",
                "day": "19",
                "month": "MAY",
                "year": "26",
                "quantity": 65,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "Exchange": "NFO",
            },
            proxy_config={"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"},
        )

        self.assertEqual(mock_place_order.call_args.args[4], "NIFTY19MAY26C24400")

    def test_alice_blue_order_response_message_is_extracted(self):
        from main.Alice_Blue_Api import _extract_alice_response_message

        message = _extract_alice_response_message({"stat": "Not_ok", "emsg": "Invalid symbol"})

        self.assertEqual(message, "Invalid symbol")

    def test_alice_blue_pre_placement_errors_are_failed(self):
        from main.Alice_Blue_Api import _alice_failed_response

        response = _alice_failed_response("Invalid LTP")

        self.assertEqual(response["data"]["status"], "Failed")
        self.assertEqual(response["data"]["message"], "Invalid LTP")

    def test_execution_engine_normalizes_nested_error_status_to_failed(self):
        from main.execution_engine import ExecutionEngine

        normalized = ExecutionEngine()._normalize_response({"data": {"status": "error", "message": "Invalid LTP"}, "job_id": 769})

        self.assertEqual(normalized["data"]["status"], "Failed")
        self.assertEqual(normalized["data"]["message"], "Invalid LTP")
        self.assertEqual(normalized["job_id"], 769)

    @mock.patch("main.Alice_Blue_Api.requests.get")
    def test_alice_blue_proxy_client_passes_proxies_to_requests(self, mock_get):
        from main.Alice_Blue_Api import ProxyAwareAliceblue

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_get.return_value = SimpleNamespace(status_code=200, text='{"stat":"Ok"}', reason="OK")
        alice = ProxyAwareAliceblue(user_id="alice-user", api_key="alice-api", proxy_config=proxy_config)
        alice._sub_urls["test"] = "test"
        alice._get("test")
        self.assertEqual(mock_get.call_args.kwargs["proxies"], proxy_config)

    @mock.patch("main.Alice_Blue_Api.requests.request")
    def test_alice_blue_websocket_session_calls_use_proxy(self, mock_request):
        from main.Alice_Blue_Api import A3_WS_CREATE_URL, A3_WS_INVALIDATE_URL, ProxyAwareAliceblue

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_request.return_value = SimpleNamespace(status_code=200, reason="OK", json=lambda: {"status": "Ok"})
        alice = ProxyAwareAliceblue(user_id="alice-user", api_key="alice-api", proxy_config=proxy_config)

        alice.invalid_sess("session-token")
        alice.createSession("session-token")

        self.assertEqual(mock_request.call_count, 2)
        self.assertEqual(mock_request.call_args_list[0].args[:2], ("POST", A3_WS_INVALIDATE_URL))
        self.assertEqual(mock_request.call_args_list[1].args[:2], ("POST", A3_WS_CREATE_URL))
        for call in mock_request.call_args_list:
            self.assertEqual(call.kwargs["proxies"], proxy_config)
            self.assertEqual(call.kwargs["headers"]["Authorization"], "Bearer session-token")
            self.assertEqual(call.kwargs["json"]["source"], "API")

    @mock.patch("builtins.open", new_callable=mock.mock_open)
    @mock.patch("main.Alice_Blue_Api.requests.get")
    def test_alice_blue_contract_master_uses_proxy(self, mock_get, mock_file):
        from main.Alice_Blue_Api import ProxyAwareAliceblue

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_get.return_value = SimpleNamespace(
            status_code=200,
            text="Exch,Token,Symbol,Trading Symbol,Expiry Date,Lot Size\n",
            reason="OK",
            raise_for_status=lambda: None,
        )
        alice = ProxyAwareAliceblue(user_id="alice-user", api_key="alice-api", proxy_config=proxy_config)

        alice.get_contract_master("NFO")

        self.assertEqual(mock_get.call_args.kwargs["proxies"], proxy_config)
        mock_file.assert_called_once_with("NFO.csv", "w")

    @mock.patch("main.Alice_Blue_Api.requests.request")
    def test_alice_blue_vendor_session_uses_a3_open_api(self, mock_request):
        from main.Alice_Blue_Api import A3_VENDOR_SESSION_URL, _build_alice_vendor_session

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_request.return_value = SimpleNamespace(
            status_code=200,
            reason="OK",
            json=lambda: {"status": "Ok", "result": [{"accessToken": "a3-access-token"}]},
        )

        alice, payload = _build_alice_vendor_session(
            "alice-user",
            "auth-code",
            "api-secret",
            proxy_config=proxy_config,
        )

        self.assertIsNotNone(alice)
        self.assertEqual(alice.alice_session_id, "a3-access-token")
        self.assertEqual(payload["status"], "Ok")
        self.assertEqual(mock_request.call_args.args[:2], ("POST", A3_VENDOR_SESSION_URL))
        self.assertEqual(mock_request.call_args.kwargs["proxies"], proxy_config)
        self.assertIn("checkSum", mock_request.call_args.kwargs["json"])

    @mock.patch("main.views.get_alice_session")
    def test_alice_blue_generate_token_redirects_to_sso_flow(self, mock_get_alice_session):
        broker = Broker.objects.create(broker_name="Alice Blue", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=broker,
            broker_API_KEY="alice-api-key",
            broker_API_UID="alice-user-id",
        )
        proxy_node = ExecutionNode.objects.create(
            name="Alice Proxy",
            ip_address="203.0.113.55",
            provider="proxy-vendor",
            node_id="alice-proxy-node",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=False,
            assigned_client=self.client_user,
            status=ExecutionNode.STATUS_ASSIGNED,
        )
        broker_details.execution_node = proxy_node
        broker_details.save(update_fields=["execution_node"])
        access_token = str(RefreshToken.for_user(self.client_user).access_token)

        response = self.client.post("/api/broker-generate-token/", HTTP_AUTHORIZATION=f"Bearer {access_token}")

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["action"], "redirect")
        self.assertEqual(payload["data"]["connect_path"], "/broker_auth_login/?broker=alice%20blue")
        mock_get_alice_session.assert_not_called()
        broker_details.refresh_from_db()
        proxy_node.refresh_from_db()
        self.assertFalse(broker_details.access_token)
        self.assertFalse(proxy_node.is_verified_with_broker)

    @mock.patch("main.Alice_Blue_Api._build_alice_vendor_session")
    @mock.patch("main.Alice_Blue_Api._build_alice_session")
    def test_alice_blue_legacy_login_is_disabled(self, mock_build_session, mock_vendor_session):
        from main.Alice_Blue_Api import get_alice_session

        alice, error = get_alice_session(
            "alice-user-id",
            "alice-api-key",
            api_secret="alice-secret",
            auth_code="stale-vendor-auth-code",
            return_error=True,
        )

        self.assertIsNone(alice)
        self.assertIn("Legacy Alice Blue API-key session generation is disabled", error)
        mock_build_session.assert_not_called()
        mock_vendor_session.assert_not_called()

    def test_alice_blue_invalid_input_message_identifies_failed_login_step(self):
        from main.Alice_Blue_Api import _describe_alice_login_failure

        user_error = _describe_alice_login_failure(
            {"stat": "Not_ok", "emsg": "Invalid Input", "alice_step": "encryption_key"}
        )
        key_error = _describe_alice_login_failure(
            {"stat": "Not_ok", "emsg": "Invalid Input", "alice_step": "get_session_data"}
        )

        self.assertIn("rejected the saved User ID", user_error)
        self.assertIn("rejected the saved ANT API_KEY", key_error)

    @mock.patch("main.Alice_Blue_Api.requests.request")
    @mock.patch("main.Alice_Blue_Api.fetch_instrument_data")
    @mock.patch("main.Alice_Blue_Api.get_alice_saved_session")
    def test_alice_blue_place_order_uses_a3_open_api(self, mock_saved_session, mock_fetch, mock_request):
        from main.Alice_Blue_Api import A3_ORDER_PLACE_URL

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        alice = SimpleNamespace(
            alice_session_id="saved-session",
            get_instrument_by_symbol=mock.Mock(return_value=SimpleNamespace(token="260520000352208")),
        )
        mock_saved_session.return_value = (alice, None)
        mock_request.return_value = SimpleNamespace(
            status_code=200,
            reason="OK",
            json=lambda: {
                "status": "Ok",
                "result": [{"brokerOrderId": "260520000352208", "status": "open", "message": "Order routed to execution node."}],
            },
        )

        response = place_alice_orders(
            None,
            None,
            "api-key",
            "alice-user",
            "NIFTY26MAY2623600CE",
            "BUY",
            "NIFTY",
            75,
            "test",
            "LIMIT",
            "INTRADAY",
            211.65,
            self.client_user,
            1,
            None,
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
            history_id="alice-a3",
            proxy_config=proxy_config,
            session_id="saved-session",
        )

        self.assertEqual(response["data"]["status"], "open")
        self.assertEqual(response["data"]["order_id"], "260520000352208")
        self.assertEqual(mock_request.call_args.args[:2], ("POST", A3_ORDER_PLACE_URL))
        self.assertEqual(mock_request.call_args.kwargs["headers"]["Authorization"], "Bearer saved-session")
        self.assertEqual(mock_request.call_args.kwargs["proxies"], proxy_config)
        order_payload = mock_request.call_args.kwargs["json"][0]
        self.assertEqual(order_payload["instrumentId"], "260520000352208")
        self.assertEqual(order_payload["orderComplexity"], "REGULAR")
        self.assertEqual(order_payload["product"], "INTRADAY")
        self.assertEqual(order_payload["price"], 211.65)

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
        mock_smart_connect.assert_called_once_with(api_key="api-key", proxies=proxy_config, timeout=15)

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

    def test_zerodha_trade_symbol_uses_weekly_nifty_format(self):
        symbol = build_trade_symbol(
            {
                "symbol": "NIFTY",
                "strike": "23600",
                "option_type": "CE",
                "day": "02",
                "month": "JUN",
                "year": "26",
                "fullyear": "2026",
            },
            "zerodha",
        )

        self.assertEqual(symbol, "NIFTY2660223600CE")

    def test_zerodha_trade_symbol_keeps_monthly_index_format(self):
        symbol = build_trade_symbol(
            {
                "symbol": "NIFTY",
                "strike": "23600",
                "option_type": "CE",
                "day": "30",
                "month": "JUN",
                "year": "26",
                "fullyear": "2026",
            },
            "zerodha",
        )

        self.assertEqual(symbol, "NIFTY26JUN23600CE")

    @mock.patch("main.brokers.groww.place_groww_orders")
    def test_groww_adapter_supports_proxy_and_passes_config(self, mock_place_order):
        broker = Broker.objects.create(broker_name="Groww", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=broker,
            access_token="groww-token",
        )
        adapter = get_broker_adapter(broker_details)
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_place_order.return_value = {"data": {"status": "open", "message": "Groww order placed successfully."}}

        response = adapter.place_order(
            {
                "symbol": "NIFTY",
                "strike": "24000",
                "option_type": "CE",
                "quantity": 75,
                "transaction_type": "BUY",
                "order_type": "LIMIT",
                "product_type": "INTRADAY",
                "day": "26",
                "month": "MAY",
                "year": "26",
                "fullyear": "2026",
                "history_id": "groww-adapter",
                "Exchange": "NFO",
            },
            proxy_config=proxy_config,
        )

        self.assertEqual(response["data"]["status"], "open")
        self.assertEqual(mock_place_order.call_args.kwargs["proxy_config"], proxy_config)
        args = mock_place_order.call_args.args
        self.assertEqual(args[2], "groww-token")
        self.assertEqual(args[3], "NIFTY26MAY24000CE")

    def test_groww_setup_uses_api_key_and_secret_not_access_token_field(self):
        spec = get_broker_setup_spec("Grow")

        self.assertEqual(spec["display_name"], "Groww")
        self.assertEqual(spec["auth_mode"], "api_key_secret")
        self.assertEqual(spec["connect_path"], "/broker_auth_login/?broker=groww")
        self.assertEqual([field["key"] for field in spec["fields"]], ["broker_API_KEY", "broker_API_SKEY"])

    @mock.patch("main.groww.time.time", return_value=1716710400)
    @mock.patch("main.groww.requests.post")
    def test_groww_access_token_generation_uses_api_key_secret_checksum(self, mock_post, mock_time):
        mock_post.return_value = SimpleNamespace(
            status_code=200,
            content=b"{}",
            json=lambda: {
                "status": "SUCCESS",
                "token": "groww-access-token",
                "tokenRefId": "token-ref-1",
                "sessionName": "AlgoView",
            },
        )

        result = generate_groww_access_token(
            "groww-api-key",
            "groww-secret",
            proxy_config={"https": "http://proxy.example.com:8080"},
        )

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["access_token"], "groww-access-token")
        self.assertEqual(mock_post.call_args.kwargs["headers"]["Authorization"], "Bearer groww-api-key")
        self.assertEqual(mock_post.call_args.kwargs["json"]["timestamp"], "1716710400")
        self.assertEqual(
            mock_post.call_args.kwargs["json"]["checksum"],
            generate_groww_checksum("groww-secret", "1716710400"),
        )

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
        self.assertEqual(kite.place_order.call_args.kwargs["price"], 10.0)
        self.assertNotIn("reference_price", kite.place_order.call_args.kwargs)

    @mock.patch("main.groww._iter_groww_instruments")
    def test_groww_trading_symbol_resolves_from_instrument_master(self, mock_instruments):
        mock_instruments.return_value = iter(
            [
                {
                    "exchange": "NSE",
                    "trading_symbol": "NIFTY25N1823400CE",
                    "instrument_type": "CE",
                    "segment": "FNO",
                    "underlying_symbol": "NIFTY",
                    "expiry_date": "2026-05-26",
                    "strike_price": "24000",
                    "buy_allowed": "1",
                    "sell_allowed": "1",
                }
            ]
        )

        resolved_symbol = resolve_groww_trading_symbol(
            exchange="NFO",
            segment="FNO",
            symbol="NIFTY",
            trade_symbol="NIFTY26MAY24000CE",
            strike=24000,
            option_type="CE",
            expiry_date="2026-05-26",
            proxy_config={"https": "http://proxy.example.com:8080"},
        )

        self.assertEqual(resolved_symbol, "NIFTY25N1823400CE")

    @mock.patch("main.groww.resolve_groww_trading_symbol", return_value="NIFTY25N1823400CE")
    @mock.patch("main.groww.requests.get")
    @mock.patch("main.groww.requests.post")
    def test_groww_place_order_saves_successful_history(self, mock_post, mock_get, mock_resolve_symbol):
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_get.side_effect = [
            SimpleNamespace(
                status_code=200,
                content=b"{}",
                json=lambda: {"status": "SUCCESS", "payload": {"NSE_NIFTY25N1823400CE": 10}},
            ),
            SimpleNamespace(
                status_code=200,
                content=b"{}",
                json=lambda: {
                    "status": "SUCCESS",
                    "payload": {
                        "groww_order_id": "GROWWORDER1",
                        "order_status": "EXECUTED",
                        "remark": "Order executed successfully",
                        "filled_quantity": 75,
                        "average_fill_price": 10.25,
                    },
                },
            ),
        ]
        mock_post.return_value = SimpleNamespace(
            status_code=200,
            content=b"{}",
            json=lambda: {
                "status": "SUCCESS",
                "payload": {
                    "groww_order_id": "GROWWORDER1",
                    "order_status": "OPEN",
                    "remark": "Order placed successfully",
                },
            },
        )

        response = place_groww_orders(
            24049,
            "Lite",
            "groww-token",
            "NIFTY26MAY24000CE",
            "BUY",
            "NIFTY",
            75,
            "strategy",
            "LIMIT",
            "INTRADAY",
            None,
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
            "groww-history-success",
            day="26",
            month="MAY",
            fullyear="2026",
            strike=24000,
            option_type="CE",
            proxy_config=proxy_config,
        )

        self.assertEqual(response["data"]["status"], "complete")
        order_payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(order_payload["trading_symbol"], "NIFTY25N1823400CE")
        self.assertEqual(order_payload["exchange"], "NSE")
        self.assertEqual(order_payload["segment"], "FNO")
        self.assertEqual(order_payload["product"], "MIS")
        self.assertEqual(order_payload["price"], 10.25)
        history = Tradeorderhistory.objects.get(history_id="groww-history-success")
        self.assertEqual(history.broker, "Groww")
        self.assertEqual(history.order_id, "GROWWORDER1")
        self.assertEqual(history.order_status, "complete")
        self.assertIsNone(history.failure_reason)

    @mock.patch("main.zerodha.fetch_nse_option_chain_ltp", return_value=None)
    @mock.patch("main.zerodha.requests.get")
    @mock.patch("main.zerodha.KiteConnect")
    def test_zerodha_option_limit_order_rejects_underlying_price_when_ltp_unavailable(self, mock_kite_class, mock_get, mock_fallback):
        from django.core.cache import cache
        from main.zerodha import place_zerodha_orders

        cache.clear()
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        kite = mock_kite_class.return_value
        kite.VARIETY_REGULAR = "regular"
        kite.profile.return_value = {"user_id": "kite-user"}
        kite.instruments.return_value = [{"tradingsymbol": "NIFTY24400CE"}]
        kite.ltp.return_value = {}
        mock_get.return_value = SimpleNamespace(status_code=200, content=b"{}", json=lambda: {"data": {}})

        response = place_zerodha_orders(
            24087.5,
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
            None,
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
            "kite-history-2",
            proxy_config=proxy_config,
        )

        self.assertEqual(response["data"]["status"], "Failed")
        self.assertIn("option live price is unavailable", response["data"]["message"])
        kite.place_order.assert_not_called()

    @mock.patch("main.zerodha.fetch_nse_option_chain_ltp", return_value=10)
    @mock.patch("main.zerodha.requests.get")
    @mock.patch("main.zerodha.KiteConnect")
    def test_zerodha_limit_order_uses_nse_option_chain_when_quote_permission_missing(self, mock_kite_class, mock_get, mock_fallback):
        from django.core.cache import cache
        from main.zerodha import place_zerodha_orders

        cache.clear()
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        kite = mock_kite_class.return_value
        kite.VARIETY_REGULAR = "regular"
        kite.profile.return_value = {"user_id": "kite-user"}
        kite.instruments.return_value = [{"tradingsymbol": "NIFTY26MAY24400CE"}]
        kite.ltp.side_effect = Exception("Insufficient permission for that call.")
        kite.place_order.return_value = "kite-order-nse-ltp"
        kite.order_history.return_value = [{"status": "COMPLETE", "transaction_type": "BUY", "average_price": 10, "filled_quantity": 65}]
        mock_get.return_value = SimpleNamespace(
            status_code=403,
            content=b"{}",
            json=lambda: {"status": "error", "message": "Insufficient permission for that call."},
        )

        response = place_zerodha_orders(
            24087.5,
            "Lite",
            "kite-access",
            "kite-api",
            "NIFTY26MAY24400CE",
            "BUY",
            "NIFTY",
            65,
            "strategy",
            "LIMIT",
            "MIS",
            None,
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
            "kite-history-nse-ltp",
            proxy_config=proxy_config,
        )

        self.assertNotEqual(response["data"]["status"], "Failed")
        self.assertEqual(kite.place_order.call_args.kwargs["price"], 10.05)
        mock_fallback.assert_called_once_with(
            "NIFTY26MAY24400CE",
            expiry_date=None,
            underlying="NIFTY",
            proxy_config=proxy_config,
            user=self.client_user,
        )

    @mock.patch("main.zerodha.KiteConnect")
    def test_zerodha_option_limit_ignores_far_explicit_price_and_uses_ltp_buffer(self, mock_kite_class):
        from main.zerodha import place_zerodha_orders

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        kite = mock_kite_class.return_value
        kite.VARIETY_REGULAR = "regular"
        kite.profile.return_value = {"user_id": "kite-user"}
        kite.instruments.return_value = [{"tradingsymbol": "NIFTY26JUN23700CE"}]
        kite.ltp.return_value = {"NFO:NIFTY26JUN23700CE": {"last_price": 200}}
        kite.place_order.return_value = "kite-order-safe-price"
        kite.order_history.return_value = [{"status": "COMPLETE", "transaction_type": "SELL", "average_price": 199, "filled_quantity": 65}]

        response = place_zerodha_orders(
            23700,
            "Lite",
            "kite-access",
            "kite-api",
            "NIFTY26JUN23700CE",
            "SELL",
            "NIFTY",
            65,
            "strategy",
            "LIMIT",
            "MIS",
            23700,
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
            "CLOSE",
            "kite-history-far-price",
            proxy_config=proxy_config,
            buffer_percentage=2.5,
        )

        self.assertNotEqual(response["data"]["status"], "Failed")
        self.assertEqual(kite.place_order.call_args.kwargs["price"], 199.0)

    @mock.patch("main.zerodha.fetch_nse_option_chain_ltp")
    @mock.patch("main.zerodha.requests.get")
    @mock.patch("main.zerodha.KiteConnect")
    def test_zerodha_limit_order_uses_shared_cached_option_ltp_when_quote_permission_missing(self, mock_kite_class, mock_get, mock_fallback):
        from django.core.cache import cache
        from main.zerodha import place_zerodha_orders

        cache.clear()
        cache_option_ltp("FINNIFTY 26100 PE 26 MAY 26", 58.3, source="upstox")
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        kite = mock_kite_class.return_value
        kite.VARIETY_REGULAR = "regular"
        kite.profile.return_value = {"user_id": "kite-user"}
        kite.instruments.return_value = [{"tradingsymbol": "FINNIFTY26MAY26100PE"}]
        kite.ltp.side_effect = Exception("Insufficient permission for that call.")
        kite.place_order.return_value = "kite-order-cached-ltp"
        kite.order_history.return_value = [{"status": "COMPLETE", "transaction_type": "BUY", "average_price": 58.3, "filled_quantity": 60}]

        response = place_zerodha_orders(
            26100,
            "Lite",
            "kite-access",
            "kite-api",
            "FINNIFTY26MAY26100PE",
            "BUY",
            "FINNIFTY",
            60,
            "strategy",
            "LIMIT",
            "MIS",
            None,
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
            "FINNIFTY",
            None,
            "OPEN",
            "kite-history-cached-ltp",
            proxy_config=proxy_config,
        )

        self.assertNotEqual(response["data"]["status"], "Failed")
        self.assertEqual(kite.place_order.call_args.kwargs["price"], 58.6)
        mock_get.assert_not_called()
        mock_fallback.assert_not_called()

    @mock.patch("main.zerodha.requests.get")
    @mock.patch("main.zerodha.KiteConnect")
    def test_zerodha_limit_order_uses_rest_ltp_fallback(self, mock_kite_class, mock_get):
        from django.core.cache import cache
        from main.zerodha import place_zerodha_orders

        cache.clear()
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        kite = mock_kite_class.return_value
        kite.VARIETY_REGULAR = "regular"
        kite.profile.return_value = {"user_id": "kite-user"}
        kite.instruments.return_value = [{"tradingsymbol": "NIFTY24400CE"}]
        kite.ltp.return_value = {}
        kite.place_order.return_value = "kite-order-rest-ltp"
        kite.order_history.return_value = [{"status": "COMPLETE", "transaction_type": "BUY", "average_price": 10, "filled_quantity": 65}]
        mock_get.return_value = SimpleNamespace(
            status_code=200,
            content=b"{}",
            json=lambda: {"data": {"NFO:NIFTY24400CE": {"last_price": 10}}},
        )

        response = place_zerodha_orders(
            24087.5,
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
            None,
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
            "kite-history-rest-ltp",
            proxy_config=proxy_config,
        )

        self.assertNotEqual(response["data"]["status"], "Failed")
        self.assertEqual(kite.place_order.call_args.kwargs["price"], 10.05)
        self.assertEqual(mock_get.call_args.kwargs["proxies"], proxy_config)

    def test_quote_ltp_parser_handles_broker_response_variants(self):
        self.assertEqual(
            extract_ltp_from_quote_payload({"data": {"NFO:NIFTY24400CE": {"lastPrice": "12.5"}}}, ("NFO:NIFTY24400CE",)),
            12.5,
        )
        self.assertEqual(
            extract_ltp_from_quote_payload({"data": {"NSE_FNO": {"12345": {"LTP": 17.25}}}}, ("NSE_FNO", "12345")),
            17.25,
        )
        self.assertEqual(
            extract_ltp_from_quote_payload({"data": [{"instrument_key": "NSE_FO|12345", "LastTradedPrice": 8.1}]}),
            8.1,
        )

    @mock.patch("main.services.option_ltp_fallback.requests.Session")
    def test_nse_option_chain_fallback_fetches_option_premium_through_proxy(self, mock_session_class):
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        session = mock_session_class.return_value.__enter__.return_value
        session.headers = {}
        session.proxies = {}
        session.get.side_effect = [
            SimpleNamespace(status_code=200, content=b""),
            SimpleNamespace(
                status_code=200,
                content=b"{}",
                json=lambda: {
                    "records": {
                        "data": [
                            {
                                "expiryDate": "26-May-2026",
                                "strikePrice": 24400,
                                "CE": {"lastPrice": 10.0},
                            }
                        ]
                    }
                },
            ),
        ]

        ltp = fetch_nse_option_chain_ltp(
            "NIFTY26MAY24400CE",
            proxy_config=proxy_config,
            user=self.client_user,
        )

        self.assertEqual(ltp, 10.0)
        self.assertEqual(session.proxies, proxy_config)

    def test_option_ltp_cache_matches_upstox_dhan_and_zerodha_symbol_formats(self):
        cache.clear()

        cached = cache_option_ltp("NIFTY 23400 PE 19 MAY 26", 188.15, source="upstox")

        self.assertEqual(cached, 188.15)
        self.assertEqual(get_cached_option_ltp("NIFTYMAY202623400PE", underlying="NIFTY"), 188.15)
        self.assertEqual(get_cached_option_ltp("NIFTY26MAY23400PE", underlying="NIFTY"), 188.15)
        self.assertEqual(get_cached_option_ltp("NIFTY19MAY26P23400", underlying="NIFTY"), 188.15)

    @mock.patch("main.zerodha.KiteConnect")
    def test_zerodha_limit_order_uses_nested_last_price_variant(self, mock_kite_class):
        from main.zerodha import place_zerodha_orders

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        kite = mock_kite_class.return_value
        kite.VARIETY_REGULAR = "regular"
        kite.profile.return_value = {"user_id": "kite-user"}
        kite.instruments.return_value = [{"tradingsymbol": "NIFTY24400CE"}]
        kite.ltp.return_value = {"data": {"NFO:NIFTY24400CE": {"lastPrice": 10}}}
        kite.place_order.return_value = "kite-order-variant"
        kite.order_history.return_value = [{"status": "COMPLETE", "transaction_type": "BUY", "average_price": 10, "filled_quantity": 65}]

        response = place_zerodha_orders(
            24087.5,
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
            None,
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
            "kite-history-variant",
            proxy_config=proxy_config,
        )

        self.assertNotEqual(response["data"]["status"], "Failed")
        self.assertEqual(kite.place_order.call_args.kwargs["price"], 10.05)

    @mock.patch("main.upstock.load_upstox_instruments")
    @mock.patch("main.upstock.requests.get")
    @mock.patch("main.upstock.requests.post")
    def test_upstox_limit_order_uses_option_ltp_not_underlying_price(self, mock_post, mock_get, mock_load_instruments):
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_load_instruments.return_value = [
            {"instrument_key": "NSE_FO|12345", "trading_symbol": "NIFTY24400CE"}
        ]
        mock_get.side_effect = [
            SimpleNamespace(
                status_code=200,
                content=b"{}",
                json=lambda: {"data": {"NSE_FO|12345": {"last_price": 10}}},
            ),
            SimpleNamespace(
                status_code=200,
                content=b"{}",
                json=lambda: {
                    "data": {
                        "status": "complete",
                        "order_id": "upstox-order-1",
                        "transaction_type": "BUY",
                        "average_price": 12.3,
                        "quantity": 65,
                    }
                },
            ),
        ]
        mock_post.return_value = SimpleNamespace(
            status_code=200,
            content=b"{}",
            json=lambda: {"status": "success", "data": {"order_id": "upstox-order-1"}},
        )

        response = place_upstox_orders(
            24087.5,
            "Lite",
            "upstox-access",
            "NIFTY24400CE",
            "BUY",
            "NIFTY",
            65,
            "strategy",
            "LIMIT",
            "MIS",
            None,
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
            "upstox-history-1",
            proxy_config=proxy_config,
        )

        self.assertNotEqual(response["data"]["status"], "Failed")
        self.assertEqual(mock_post.call_args.args[0], "https://api.upstox.com/v2/order/place")
        placed_payload = mock_post.call_args.kwargs["json"]
        self.assertEqual(placed_payload["price"], 10.25)
        self.assertNotIn("reference_price", placed_payload)

    @mock.patch("main.upstock.load_upstox_instruments")
    @mock.patch("main.upstock.requests.get")
    @mock.patch("main.upstock.requests.post")
    def test_upstox_order_timeout_returns_clear_failure(self, mock_post, mock_get, mock_load_instruments):
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_load_instruments.return_value = [
            {"instrument_key": "NSE_FO|12345", "trading_symbol": "NIFTY24400CE"}
        ]
        mock_get.return_value = SimpleNamespace(
            status_code=200,
            content=b"{}",
            json=lambda: {"data": {"NSE_FO|12345": {"last_price": 10}}},
        )
        mock_post.side_effect = requests.Timeout("read timeout")

        response = place_upstox_orders(
            24087.5,
            "Lite",
            "upstox-access",
            "NIFTY24400CE",
            "BUY",
            "NIFTY",
            65,
            "strategy",
            "LIMIT",
            "MIS",
            None,
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
            "upstox-timeout-history",
            proxy_config=proxy_config,
        )

        self.assertEqual(response["data"]["status"], "Failed")
        self.assertIn("timed out before broker confirmation", response["data"]["message"])

    @mock.patch("main.upstock.load_upstox_instruments")
    @mock.patch("main.upstock.requests.get")
    @mock.patch("main.upstock.requests.post")
    def test_upstox_option_limit_order_rejects_underlying_price_when_ltp_unavailable(self, mock_post, mock_get, mock_load_instruments):
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        mock_load_instruments.return_value = [
            {"instrument_key": "NSE_FO|12345", "trading_symbol": "NIFTY24400CE"}
        ]
        mock_get.return_value = SimpleNamespace(status_code=200, content=b"{}", json=lambda: {"data": {}})

        response = place_upstox_orders(
            24087.5,
            "Lite",
            "upstox-access",
            "NIFTY24400CE",
            "BUY",
            "NIFTY",
            65,
            "strategy",
            "LIMIT",
            "MIS",
            None,
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
            "upstox-history-2",
            proxy_config=proxy_config,
        )

        self.assertEqual(response["data"]["status"], "Failed")
        self.assertIn("option live price is unavailable", response["data"]["message"])
        mock_post.assert_not_called()

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

    @mock.patch("main.dhanapi.requests.post")
    @mock.patch("main.dhanapi.get_trading_symbol_security_id")
    @mock.patch("main.dhanapi.dhanhq")
    def test_dhan_order_client_receives_proxy_config(self, mock_dhan_class, mock_security_lookup, mock_post):
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
        mock_post.return_value = SimpleNamespace(status_code=200, content=b"{}", json=lambda: {"data": {"NSE_FNO": {"12345": {"last_price": 10}}}})
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

    @mock.patch("main.dhanapi.sleep")
    @mock.patch("main.dhanapi.requests.post")
    @mock.patch("main.dhanapi.get_trading_symbol_security_id")
    @mock.patch("main.dhanapi.dhanhq")
    def test_dhan_order_polls_transit_until_rejected_message(self, mock_dhan_class, mock_security_lookup, mock_post, mock_sleep):
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
        mock_post.return_value = SimpleNamespace(status_code=200, content=b"{}", json=lambda: {"data": {"NSE_FNO": {"12345": {"last_price": 10}}}})
        dhan.place_order.return_value = {"status": "success", "data": {"orderId": "dhan-order-2"}}
        dhan.get_order_by_id.side_effect = [
            {"status": "success", "data": [{"orderStatus": "TRANSIT", "transactionType": "BUY", "quantity": 65}]},
            {
                "status": "success",
                "data": [{
                    "orderStatus": "REJECTED",
                    "transactionType": "BUY",
                    "quantity": 65,
                    "omsErrorDescription": "rms: insufficient funds",
                }],
            },
        ]
        mock_security_lookup.return_value = {"status": "success", "SECURITY_ID": 12345}

        response = place_dhan_orders(
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
            "dhan-history-poll",
            proxy_config=proxy_config,
        )

        self.assertEqual(response["data"]["status"], "rejected")
        self.assertEqual(response["data"]["message"], "rms: insufficient funds")
        self.assertEqual(dhan.get_order_by_id.call_count, 2)
        self.assertEqual(mock_sleep.call_count, 1)

    @mock.patch("main.dhanapi.fetch_nse_option_chain_ltp", return_value=None)
    @mock.patch("main.dhanapi.requests.post")
    @mock.patch("main.dhanapi.get_trading_symbol_security_id")
    @mock.patch("main.dhanapi.dhanhq")
    def test_dhan_option_limit_order_rejects_underlying_price_when_ltp_unavailable(self, mock_dhan_class, mock_security_lookup, mock_post, mock_fallback):
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
        dhan.get_ltp_data.return_value = {"data": {"NSE_FNO": {}}}
        mock_post.return_value = SimpleNamespace(status_code=200, content=b"{}", json=lambda: {"data": {"NSE_FNO": {}}})
        mock_security_lookup.return_value = {"status": "success", "SECURITY_ID": 12345}

        response = place_dhan_orders(
            "2026-05-12",
            24087.5,
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
            None,
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
            "dhan-history-2",
            proxy_config=proxy_config,
        )

        self.assertEqual(response["data"]["status"], "Failed")
        self.assertIn("option live price is unavailable", response["data"]["message"])
        dhan.place_order.assert_not_called()

    @mock.patch("main.dhanapi.fetch_nse_option_chain_ltp", return_value=10)
    @mock.patch("main.dhanapi.requests.post")
    @mock.patch("main.dhanapi.get_trading_symbol_security_id")
    @mock.patch("main.dhanapi.dhanhq")
    def test_dhan_limit_order_uses_nse_option_chain_when_data_api_missing(self, mock_dhan_class, mock_security_lookup, mock_post, mock_fallback):
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
        dhan.get_ltp_data.return_value = {"data": {"NSE_FNO": {}}}
        mock_post.return_value = SimpleNamespace(
            status_code=401,
            content=b"{}",
            json=lambda: {"status": "failed", "data": {"806": "Data APIs not Subscribed"}},
        )
        mock_security_lookup.return_value = {"status": "success", "SECURITY_ID": 12345}
        dhan.place_order.return_value = {"status": "success", "data": {"orderId": "dhan-order-nse-ltp"}}
        dhan.get_order_by_id.return_value = {
            "status": "success",
            "data": [{"orderStatus": "TRADED", "transactionType": "BUY", "averageTradedPrice": 10, "quantity": 65}],
        }

        response = place_dhan_orders(
            "2026-05-26",
            24087.5,
            "Lite",
            "dhan-access",
            "dhan-client",
            "NIFTY-May2026-24400-CE",
            "BUY",
            "NIFTY",
            65,
            "strategy",
            "LIMIT",
            "MIS",
            None,
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
            "dhan-history-nse-ltp",
            proxy_config=proxy_config,
        )

        self.assertNotEqual(response["data"]["status"], "Failed")
        self.assertEqual(dhan.place_order.call_args.kwargs["price"], 10.25)
        mock_fallback.assert_called_once_with(
            "NIFTY-May2026-24400-CE",
            expiry_date="2026-05-26",
            underlying="NIFTY",
            proxy_config=proxy_config,
            user=self.client_user,
        )

    @mock.patch("main.dhanapi.requests.post")
    @mock.patch("main.dhanapi.get_trading_symbol_security_id")
    @mock.patch("main.dhanapi.dhanhq")
    def test_dhan_limit_order_uses_nested_ltp_variant(self, mock_dhan_class, mock_security_lookup, mock_post):
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
        dhan.get_ltp_data.return_value = {"data": {"NSE_FNO": {"12345": {"lastPrice": 10}}}}
        mock_post.return_value = SimpleNamespace(status_code=200, content=b"{}", json=lambda: {"data": {"NSE_FNO": {"12345": {"lastPrice": 10}}}})
        dhan.place_order.return_value = {"status": "success", "data": {"orderId": "dhan-order-variant"}}
        dhan.get_order_by_id.return_value = {
            "status": "success",
            "data": [{"orderStatus": "TRADED", "transactionType": "BUY", "averageTradedPrice": 10, "quantity": 65}],
        }
        mock_security_lookup.return_value = {"status": "success", "SECURITY_ID": 12345}

        response = place_dhan_orders(
            "2026-05-12",
            24087.5,
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
            None,
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
            "dhan-history-variant",
            proxy_config=proxy_config,
        )

        self.assertNotEqual(response["data"]["status"], "Failed")
        self.assertEqual(dhan.place_order.call_args.kwargs["price"], 10.25)
        self.assertEqual(mock_post.call_args.kwargs["proxies"], proxy_config)

    @mock.patch("main.dhanapi.ensure_dhan_instruments_file")
    def test_dhan_security_lookup_ignores_invalid_placeholder_expiry_dates(self, mock_instrument_file):
        with tempfile.NamedTemporaryFile("w", suffix=".csv", delete=False) as file_obj:
            file_obj.write(
                "SEM_EXM_EXCH_ID,SEM_SEGMENT,SEM_SMST_SECURITY_ID,SEM_INSTRUMENT_NAME,SEM_EXPIRY_CODE,"
                "SEM_TRADING_SYMBOL,SEM_LOT_UNITS,SEM_CUSTOM_SYMBOL,SEM_EXPIRY_DATE,SEM_STRIKE_PRICE,"
                "SEM_OPTION_TYPE,SEM_TICK_SIZE,SEM_EXPIRY_FLAG,SEM_EXCH_INSTRUMENT_TYPE,SEM_SERIES,SM_SYMBOL_NAME\n"
            )
            file_obj.write(
                "NSE,E,999,INDEX,0,NIFTY,1,NIFTY,0001-01-01,0,XX,0.05,M,INDEX,,NIFTY\n"
            )
            file_obj.write(
                "NSE,D,41746,OPTIDX,0,NIFTY-May2026-23900-CE,65,NIFTY 12 MAY 23900 CALL,"
                "2026-05-12 14:30:00,23900.0,CE,0.05,W,OPTIDX,,NIFTY\n"
            )
            csv_path = file_obj.name

        mock_instrument_file.return_value = csv_path
        try:
            result = get_trading_symbol_security_id("NIFTYMAY202623900CE", None, "NFO", "2026-05-12", self.client_user)
        finally:
            os.unlink(csv_path)

        self.assertEqual(result["status"], "success")
        self.assertEqual(int(result["SECURITY_ID"]), 41746)

    def test_all_supported_brokers_have_execution_node_adapters(self):
        broker_names = {
            "Upstox": "upstox",
            "Zerodha": "zerodha",
            "Groww": "groww",
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

    def test_proxy_config_removes_invisible_paste_marks(self):
        node = ExecutionNode(
            name="Copied Proxy Node",
            ip_address="2401:c080:2400:1e3d:815f:789:3fe8:f043",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="\u2060\u202fdc-mum-600.staticip.in",
            proxy_port=443,
            proxy_protocol=" HTTP\u200b",
            proxy_username="5V5boNvhvVcW4280MYS5X\u200b",
        )
        node.set_proxy_password("f645e35e60c747f9a48f371f700d5d07")
        config = build_requests_proxy_config(node)
        self.assertEqual(
            config["https"],
            "http://5V5boNvhvVcW4280MYS5X:f645e35e60c747f9a48f371f700d5d07@dc-mum-600.staticip.in:443",
        )

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

    def test_login_token_flow_can_use_verified_proxy_before_broker_verification(self):
        proxy_node = ExecutionNode.objects.create(
            name="Dhan Login Proxy",
            ip_address="10.0.0.31",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=False,
        )
        assign_execution_node_to_client(self.client_user, proxy_node)
        self.broker_details.refresh_from_db()

        self.assertIsNone(_broker_proxy_config_or_none(self.broker_details))
        proxy_config = _broker_proxy_config_or_none(self.broker_details, require_broker_verified=False)
        self.assertIn("https", proxy_config)

    def test_successful_token_generation_marks_execution_node_broker_verified(self):
        proxy_node = ExecutionNode.objects.create(
            name="Dhan Token Proxy",
            ip_address="10.0.0.32",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=False,
        )
        assign_execution_node_to_client(self.client_user, proxy_node)
        self.broker_details.refresh_from_db()

        _save_session_tokens_compat(self.broker_details, "request-token", "access-token")

        proxy_node.refresh_from_db()
        self.assertTrue(proxy_node.is_verified_with_broker)

    def test_clear_session_tokens_removes_legacy_token_fields(self):
        self.broker_details.access_token = "legacy-access"
        self.broker_details.refreshToken = "legacy-refresh"
        self.broker_details.feed_token = "legacy-feed"
        self.broker_details.set_session_tokens("secure-access", refresh_token="secure-refresh", feed_token="secure-feed")

        self.broker_details.clear_session_tokens()

        self.assertIsNone(self.broker_details.get_access_token_secure())
        self.assertIsNone(self.broker_details.get_refresh_token_secure())
        self.assertIsNone(self.broker_details.get_feed_token_secure())
        self.assertIsNone(self.broker_details.access_token)
        self.assertIsNone(self.broker_details.refreshToken)
        self.assertIsNone(self.broker_details.feed_token)
        self.assertTrue(self.broker_details.isTokenExpired)

    def test_sl_tp_watch_result_builds_entry_price_without_instance_self(self):
        trade_order = SimpleNamespace(
            id=1,
            client=self.client_user,
            client_id=self.client_user.id,
            broker="Angel One",
            Index_Symbol="NIFTY",
            trading_symbol="NIFTY26JUN24000CE",
            GroupService="",
            Entry_Price="123.45",
            LivePrice="124.00",
            EntryQty="50",
            ExitQty=None,
        )

        result = SLTPWatcherService._build_watch_result(
            trade_order,
            status="skipped",
            message="No active stop-loss or target is configured.",
        )

        self.assertEqual(result.entry_price, 123.45)
        self.assertEqual(result.quantity, 50)

    def test_sl_tp_success_statuses_include_routed_open_order(self):
        self.assertIn("open", SUCCESS_EXIT_STATUSES)

    def test_sl_tp_exit_request_uses_separate_history_id(self):
        trade_order = SimpleNamespace(
            id=1,
            history_id="buy-history-1",
            client=self.client_user,
            GroupService="",
            trading_symbol="NIFTY26JUN24000CE",
            Index_Symbol="NIFTY",
            EntryQty=50,
            Entry_type=None,
            Entry_Price="123.45",
            Lot=1,
            strategy="test",
            Exchange="NFO",
            Segment="FNO",
            order_params={},
        )
        trade_setting = SimpleNamespace(
            expiry_date=timezone.datetime(2026, 6, 26),
            strategy="test",
            order_type="LIMIT",
            product_type="INTRADAY",
            quantity=50,
        )

        request = SLTPWatcherService()._build_exit_request(
            trade_order=trade_order,
            trade_setting=trade_setting,
            current_ltp=130,
            trigger_reason="TARGET",
            stop_loss_price=None,
            target_price=130,
        )

        self.assertEqual(request.history_id, "buy-history-1_sltp_exit")
        self.assertEqual(request.webhook_signal["original_history_id"], "buy-history-1")
        self.assertEqual(request.transaction_type, "SELL")

    def test_sl_tp_exit_request_prefers_stored_contract_metadata(self):
        trade_order = SimpleNamespace(
            id=1,
            history_id="alice-buy-history",
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="BANKNIFTY53400CE",
            Index_Symbol="BANKNIFTY53400CE",
            EntryQty=30,
            Entry_type=None,
            Entry_Price="1334.55",
            Lot=1,
            strategy="test",
            Exchange="NFO",
            Segment="FNO",
            order_params={
                "symbol": "BANKNIFTY",
                "expiry": "2026-06-30",
                "strike": 53400,
                "option_type": "CE",
                "product_type": "MIS",
            },
        )
        trade_setting = SimpleNamespace(
            expiry_date=timezone.datetime(2026, 6, 1),
            strategy="test",
            order_type="LIMIT",
            product_type="MIS",
            quantity=30,
        )

        request = SLTPWatcherService()._build_exit_request(
            trade_order=trade_order,
            trade_setting=trade_setting,
            current_ltp=1297.9,
            trigger_reason="STOP_LOSS",
            stop_loss_price=1314.55,
            target_price=1374.55,
        )

        self.assertEqual(request.day, "30")
        self.assertEqual(request.month, "JUN")
        self.assertEqual(request.year, "26")
        self.assertEqual(request.symbol, "BANKNIFTY")
        self.assertEqual(request.strike, 53400)
        self.assertEqual(request.option_type, "CE")

    @mock.patch("main.dematemodule._broker_proxy_config_or_none", return_value={"https": "http://proxy.example.com:8080"})
    @mock.patch("main.dematemodule._create_broker_callback_state", return_value="alice-callback-state")
    def test_alice_blue_redirect_does_not_mark_token_created(self, mock_create_state, mock_proxy_config):
        alice = Broker.objects.create(broker_name="Alice Blue", is_active=True)
        old_token_time = timezone.now() - timezone.timedelta(days=2)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=alice,
            broker_API_KEY="alice-app-code",
            broker_API_SKEY="alice-secret",
            broker_API_UID="alice-user",
        )
        ClientBrokerdetails.objects.filter(pk=broker_details.pk).update(tokenCreatedAt=old_token_time)
        broker_details.refresh_from_db()

        response = BrokerLoginRedirectView().redirect_to_alice_blue(SimpleNamespace(), broker_details)

        self.assertEqual(response.status_code, 200)
        broker_details.refresh_from_db()
        self.assertEqual(broker_details.request_token, "alice-callback-state")
        self.assertEqual(broker_details.tokenCreatedAt, old_token_time)
        mock_create_state.assert_called_once()
        mock_proxy_config.assert_called_once_with(broker_details, require_broker_verified=False)

    @mock.patch("main.dematemodule.requests.post")
    def test_upstox_token_flow_uses_verified_proxy_before_broker_verification(self, mock_post):
        upstox = Broker.objects.create(broker_name="Upstox", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=upstox,
            broker_API_KEY="upstox-key",
            broker_API_SKEY="upstox-secret",
            broker_Demate_User_Name="upstox-user",
        )
        proxy_node = ExecutionNode.objects.create(
            name="Upstox Token Proxy",
            ip_address="10.0.0.33",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=False,
        )
        assign_execution_node_to_client(self.client_user, proxy_node)
        broker_details.refresh_from_db()
        mock_post.return_value = SimpleNamespace(
            status_code=200,
            content=b"{}",
            json=lambda: {"access_token": "upstox-access", "refresh_token": "upstox-refresh", "expires_in": 3600},
        )

        response = BrokerCallbackView().handle_upstox("auth-code", broker_details)

        self.assertEqual(response.status_code, 200)
        mock_post.assert_called_once()
        self.assertIn("proxies", mock_post.call_args.kwargs)
        proxy_node.refresh_from_db()
        self.assertTrue(proxy_node.is_verified_with_broker)

    def test_dhan_setup_accepts_manual_token_without_api_secret_pair(self):
        dhan = Broker.objects.create(broker_name="Dhan", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(client=self.client_user, broker_name=dhan)

        serializer = ClientBrokerDetailsUpdateSerializer(
            broker_details,
            data={"access_token": "direct-dhan-token"},
            partial=True,
        )

        self.assertTrue(serializer.is_valid(), serializer.errors)
        serializer.save()
        broker_details.refresh_from_db()
        self.assertEqual(broker_details.access_token, "direct-dhan-token")

    def test_dhan_setup_schema_documents_either_token_or_consent_credentials(self):
        spec = get_broker_setup_spec("dhan")
        fields = {field["key"]: field for field in spec["fields"]}
        self.assertFalse(fields["broker_API_KEY"]["required"])
        self.assertFalse(fields["broker_API_SKEY"]["required"])
        self.assertFalse(fields["broker_API_UID"]["required"])
        self.assertFalse(fields["access_token"]["required"])
        self.assertIn("either Access Token", spec["requirement_note"])

    def test_egress_guard_allows_public_instrument_masters_for_expiry_lists(self):
        angel_master = "https://margincalculator.angelbroking.com/OpenAPI_File/files/OpenAPIScripMaster.json"
        self.assertTrue(_is_broker_url(angel_master))
        self.assertTrue(_is_public_instrument_master_url(angel_master))
        self.assertTrue(_is_public_instrument_master_url("https://assets.upstox.com/market-quote/instruments/exchange/NSE.json.gz"))
        self.assertTrue(_is_public_instrument_master_url("https://images.dhan.co/api-data/api-scrip-master.csv"))
        self.assertFalse(_is_public_instrument_master_url("https://api.dhan.co/v2/orders"))

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
        self.assertTrue(adapter_factory.return_value.place_order.call_args.args[0]["_allow_direct_node_execution"])

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
        self.assertIn("Proxy/static-IP", place_groww_orders(access_token="t", trade_symbol="NIFTY", **common)["data"]["message"])
        self.assertIn(
            "Proxy/static-IP",
            place_5paisa_order(api_key="k", access_token="t", trade_symbol="NIFTY", trade=SimpleNamespace(), **common)["data"]["message"],
        )
        self.assertIn(
            "Proxy/static-IP",
            place_alice_orders(
                None,
                None,
                "k",
                "u",
                "NIFTY",
                "BUY",
                "NIFTY",
                1,
                "test",
                "LIMIT",
                "INTRADAY",
                1,
                self.client_user,
                1,
                None,
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
                history_id="no-proxy",
            )["data"]["message"],
        )

    def test_live_price_cache_rejects_stale_ticks(self):
        payload = build_live_price_payload(
            instrument_key="NSE_FO|123",
            ltp=101.5,
            source="test",
            trading_symbol="NIFTY 24000 CE 26 MAY 26",
            underlying="NIFTY",
            expiry_date=timezone.datetime(2026, 5, 26),
            strike=24000,
            option_type="CE",
        )
        cache_live_price(payload, aliases=("NIFTY26MAY2624000CE",))

        fresh = get_live_price(trading_symbol="NIFTY26MAY2624000CE", max_age_seconds=5)
        stale = get_live_price(trading_symbol="NIFTY26MAY2624000CE", max_age_seconds=0)

        self.assertEqual(fresh["ltp"], 101.5)
        self.assertTrue(fresh["is_fresh"])
        self.assertFalse(stale["is_fresh"])

    @mock.patch("main.services.upstox_market_data.load_upstox_instruments")
    def test_upstox_market_data_resolves_open_trade_instrument_once(self, mock_load):
        mock_load.side_effect = lambda exchange: [
            {
                "instrument_key": f"{exchange}_FO|123",
                "trading_symbol": "NIFTY 24000 CE 26 MAY 26",
                "instrument_type": "CE",
                "underlying_symbol": "NIFTY",
                "expiry": int(timezone.datetime(2026, 5, 26, tzinfo=timezone.get_current_timezone()).timestamp() * 1000),
                "strike_price": 24000,
                "exchange": exchange,
            }
        ] if exchange == "NSE" else []
        Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY26MAY2624000CE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            order_id="open-1",
            order_status="completed",
            trade_order_status="OPEN",
        )

        instruments = get_active_option_instruments()

        self.assertEqual(len(instruments), 1)
        self.assertEqual(instruments[0].instrument_key, "NSE_FO|123")
        self.assertEqual(UpstoxInstrumentResolver().resolve("NIFTY 24000 CE 26 MAY 26").instrument_key, "NSE_FO|123")
