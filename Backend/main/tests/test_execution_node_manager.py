import os
import json
import tempfile
import time
from datetime import datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import requests
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import TestCase, override_settings
from django.utils import timezone
from rest_framework_simplejwt.tokens import RefreshToken

from main.brokers.base import get_broker_adapter
from main.models import Broker, ChatMessage, ChatThread, ClientBrokerdetails, ClientTradeSetting, ExecutionNode, ExecutionNodeAssignment, ExecutionOrderJob, Role, Tradeorderhistory, TradingLog, User
from main.services.execution_nodes import assign_execution_node_to_client, mark_execution_node_broker_verified_from_valid_token, release_execution_node
from main.services.execution_router import route_order_to_execution_node
from main.services.egress_guard import _is_broker_url, _is_public_instrument_master_url
from main.services.node_security import generate_node_signature, verify_node_signature
from main.services.proxy_utils import build_requests_proxy_config, mask_proxy_url, verify_proxy_public_ip
from main.fyersapi import place_fyers_orders
from main.upstock import _positive_number_or_none, handle_successful_order, place_upstox_orders
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
from main.brokers.position_guard import find_matching_open_buy_position, mark_open_position_closed, prepare_close_order_from_open_position, remaining_open_quantity
from main.permissions import can_access_client_record
from main.services.live_price_cache import build_live_price_payload, cache_live_price, get_live_price
from main.services.option_ltp_fallback import cache_option_ltp, fetch_nse_option_chain_ltp, get_cached_option_ltp
from main.sl_tp_watcher_service import SLTPWatcherService, SUCCESS_EXIT_STATUSES
from main.services.upstox_market_data import UpstoxInstrumentResolver, _parse_option_symbol, get_active_option_instruments
from main.serializers import ClientBrokerDetailsUpdateSerializer, TradeorderhistorySerializer
from main.trade_history_service import save_trade_order_history
from main.views import _build_regular_trade_exit_request, _is_regular_trade_open, _process_webhook_trade, _resolve_webhook_request_context, place_order_broker
from main.tasks import process_single_webhook_trade_task, process_webhook_signal_task, schedule_broker_session_warmup
from main.angelone.managers.contract_manager import ContractMasterManager


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

    def test_angel_contract_master_refresh_writes_disk_cache(self):
        with tempfile.TemporaryDirectory() as tmpdir, override_settings(BASE_DIR=tmpdir):
            ContractMasterManager._instance = None
            manager = ContractMasterManager.get_instance()
            payload = [
                {
                    "token": "51379",
                    "symbol": "NIFTY14JUL2624200CE",
                    "name": "NIFTY",
                    "expiry": "14JUL2026",
                    "strike": "2420000",
                    "lotsize": "65",
                    "instrumenttype": "OPTIDX",
                    "exch_seg": "NFO",
                    "tick_size": "0.05",
                }
            ]
            response = mock.Mock()
            response.json.return_value = payload
            response.raise_for_status.return_value = None

            with mock.patch("main.angelone.managers.contract_manager.requests.get", return_value=response):
                self.assertTrue(manager._refresh_contracts())

            cache_path = manager._cache_path()
            self.assertTrue(cache_path.exists())
            contract, match = manager.resolve_option_contract("NIFTY", 24200, "CE", expiry=datetime(2026, 7, 14))
            self.assertEqual(contract.token, "51379")
            self.assertEqual(match["match_type"], "exact")

    def test_angel_contract_master_uses_disk_cache_when_refresh_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir, override_settings(BASE_DIR=tmpdir):
            ContractMasterManager._instance = None
            manager = ContractMasterManager.get_instance()
            cache_path = manager._cache_path()
            cache_path.parent.mkdir(parents=True, exist_ok=True)
            cache_path.write_text(
                json.dumps([
                    {
                        "token": "51379",
                        "symbol": "NIFTY14JUL2624200CE",
                        "name": "NIFTY",
                        "expiry": "14JUL2026",
                        "strike": "2420000",
                        "lotsize": "65",
                        "instrumenttype": "OPTIDX",
                        "exch_seg": "NFO",
                        "tick_size": "0.05",
                    }
                ]),
                encoding="utf-8",
            )

            with mock.patch("main.angelone.managers.contract_manager.requests.get", side_effect=requests.ConnectionError("download failed")):
                self.assertTrue(manager.initialize(blocking=True))

            contract, match = manager.resolve_option_contract("NIFTY", 24200, "CE", expiry=datetime(2026, 7, 14))
            self.assertEqual(contract.symbol, "NIFTY14JUL2624200CE")
            self.assertEqual(match["match_type"], "exact")

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

    def test_trade_history_serializer_total_uses_closed_quantity(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY26MAY2624000CE",
            order_status="complete",
            trade_order_status="CLOSE",
            Entry_type="BUY",
            Entry_Price=Decimal("100.00"),
            Exit_Price=Decimal("90.00"),
            EntryQty=65,
            ExitQty=30,
        )

        data = TradeorderhistorySerializer(history).data

        self.assertEqual(data["Total"], "-300.00")

    def test_legacy_exit_quantity_does_not_block_an_open_buy(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY26MAY2624000CE",
            transaction_type="BUY",
            order_status="complete",
            trade_order_status="OPEN",
            order_id="legacy-open-buy",
            Entry_Price=Decimal("100.00"),
            EntryQty=65,
            ExitQty=65,
            Exit_status="Pending",
        )

        self.assertEqual(remaining_open_quantity(history), 65)
        self.assertTrue(_is_regular_trade_open(history))

    def test_confirmed_exit_quantity_still_closes_the_buy_allocation(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY26MAY2624000CE",
            transaction_type="BUY",
            order_status="complete",
            trade_order_status="CLOSE",
            order_id="confirmed-closed-buy",
            Entry_Price=Decimal("100.00"),
            EntryQty=65,
            Exit_Price=Decimal("110.00"),
            ExitQty=65,
            Exit_status="COMPLETED",
        )

        self.assertEqual(remaining_open_quantity(history), 0)

    def test_selected_close_matches_generic_symbol_using_saved_strike(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="manual-dhan-generic-symbol",
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY",
            broker="Dhan",
            transaction_type="BUY",
            order_status="traded",
            trade_order_status="OPEN",
            order_id="dhan-entry-order",
            Entry_Price=Decimal("109.20"),
            EntryQty=65,
            order_params={
                "symbol": "NIFTY",
                "strike": 24300.0,
                "option_type": "PE",
                "expiry": "2026-08-04",
                "product_type": "MIS",
            },
        )
        close_order = {
            "transaction_type": "SELL",
            "symbol": "NIFTY",
            "strike": 24300.0,
            "option_type": "PE",
            "quantity": 65,
            "order_params": {"original_history_id": history.history_id},
        }

        prepared, matched_history, error = prepare_close_order_from_open_position(
            self.client_user,
            close_order,
            "dhan",
        )

        self.assertIsNone(error)
        self.assertEqual(matched_history.id, history.id)
        self.assertEqual(prepared["quantity"], 65)
        self.assertEqual(prepared["strike"], "24300")

    def test_trade_history_serializer_backfills_missing_exit_quantity_for_completed_close(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY26MAY2623200CE",
            order_status="complete",
            trade_order_status="CLOSE",
            Entry_Price=Decimal("250.00"),
            Exit_Price=Decimal("230.00"),
            EntryQty=65,
            ExitQty=None,
        )

        data = TradeorderhistorySerializer(history).data

        self.assertEqual(data["ExitQty"], 65)
        self.assertEqual(data["Total"], "-1300.00")

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

    def test_trade_history_failure_cannot_overwrite_broker_confirmed_fill(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="confirmed-fill-history",
            trading_symbol="BANKNIFTY",
            order_id="broker-order-1",
            order_status="complete",
            trade_order_status="OPEN",
            Entry_status="complete",
            Entry_Price=Decimal("1006.15"),
            EntryQty=30,
            response_data={"data": {"status": "complete", "order_id": "broker-order-1"}},
        )

        save_trade_order_history(
            1004.55,
            "test",
            "BUY",
            "Failed",
            self.client_user,
            "BANKNIFTY",
            0,
            "Failed",
            {"data": {"status": "Failed", "message": "Daily trade limit reached."}},
            "Daily trade limit reached.",
            "test-strategy",
            "BUY",
            None,
            None,
            None,
            30,
            None,
            {},
            "NFO",
            "OPT",
            "BANKNIFTY26AUG57000CE",
            {"quantity": 30},
            broker="Zerodha",
            history_id=history.history_id,
        )

        history.refresh_from_db()
        self.assertEqual(history.order_status, "complete")
        self.assertEqual(history.trade_order_status, "OPEN")
        self.assertEqual(history.order_id, "broker-order-1")
        self.assertEqual(history.Entry_Price, Decimal("1006.15"))
        self.assertIsNone(history.failure_reason)
        self.assertEqual(history.response_data["data"]["status"], "complete")

    def test_trade_history_risk_failure_cannot_overwrite_accepted_broker_order(self):
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="accepted-order-history",
            trading_symbol="BANKNIFTY",
            order_id="broker-order-2",
            order_status="open",
            trade_order_status="OPEN",
            Entry_status="open",
            Entry_Price=Decimal("1008.90"),
            EntryQty=30,
            response_data={"data": {"status": "open", "order_id": "broker-order-2"}},
        )

        save_trade_order_history(
            1008.90,
            "test",
            "BUY",
            "Failed",
            self.client_user,
            "BANKNIFTY",
            0,
            "Failed",
            {"data": {"status": "Failed", "message": "Daily trade limit reached."}},
            "Daily trade limit reached.",
            "test-strategy",
            "BUY",
            None,
            None,
            None,
            30,
            None,
            {},
            "NFO",
            "OPT",
            "BANKNIFTY25AUG2657000CE",
            {"quantity": 30},
            broker="Angel One",
            history_id=history.history_id,
        )

        history.refresh_from_db()
        self.assertEqual(history.order_status, "open")
        self.assertEqual(history.trade_order_status, "OPEN")
        self.assertEqual(history.order_id, "broker-order-2")
        self.assertIsNone(history.failure_reason)

    def test_force_kill_open_submission_does_not_mark_trade_closed(self):
        from main.views import _mark_trade_closed_after_force_exit

        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="BANKNIFTY25AUG2657000CE",
            order_id="entry-order-1",
            order_status="complete",
            trade_order_status="OPEN",
            Entry_Price=Decimal("1008.20"),
            EntryQty=30,
        )

        marked = _mark_trade_closed_after_force_exit(
            history,
            {
                "data": {
                    "status": "open",
                    "order_id": "provisional-exit-order",
                    "price": 984.65,
                }
            },
        )

        history.refresh_from_db()
        self.assertFalse(marked)
        self.assertEqual(history.trade_order_status, "OPEN")
        self.assertIsNone(history.Exit_Price)
        self.assertIsNone(history.ExitQty)

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

    def test_subadmin_can_view_webhook_diagnostics_for_assigned_clients_only(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        subadmin = User.objects.create_user(
            email="diagnostics-subadmin@example.com",
            firstName="Diagnostics",
            lastName="Sub",
            phoneNumber="9999999920",
            password="Pass@123",
            role=subadmin_role,
        )
        assigned_client = User.objects.create_user(
            email="diagnostics-assigned@example.com",
            firstName="Diagnostics",
            lastName="Assigned",
            phoneNumber="9999999921",
            password="Pass@123",
            type_of_user="is_client",
            is_client=True,
            assigned_client=subadmin,
        )
        other_client = User.objects.create_user(
            email="diagnostics-other@example.com",
            firstName="Diagnostics",
            lastName="Other",
            phoneNumber="9999999922",
            password="Pass@123",
            type_of_user="is_client",
            is_client=True,
        )
        ClientTradeSetting.objects.create(client=assigned_client, symbol="NIFTY", broker="Angel One", quantity=65)
        ClientTradeSetting.objects.create(client=other_client, symbol="BANKNIFTY", broker="Zerodha", quantity=30)

        access_token = str(RefreshToken.for_user(subadmin).access_token)
        response = self.client.get(
            "/api/webhook-diagnostics/",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        client_ids = {item["client_id"] for item in response.data["data"]}
        self.assertIn(assigned_client.id, client_ids)
        self.assertNotIn(other_client.id, client_ids)

    def test_subadmin_can_view_sltp_watcher_for_assigned_clients_only(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        subadmin = User.objects.create_user(
            email="sltp-subadmin@example.com",
            firstName="Sltp",
            lastName="Sub",
            phoneNumber="9999999923",
            password="Pass@123",
            role=subadmin_role,
        )
        assigned_client = User.objects.create_user(
            email="sltp-assigned@example.com",
            firstName="Sltp",
            lastName="Assigned",
            phoneNumber="9999999924",
            password="Pass@123",
            type_of_user="is_client",
            is_client=True,
            assigned_client=subadmin,
        )
        other_client = User.objects.create_user(
            email="sltp-other@example.com",
            firstName="Sltp",
            lastName="Other",
            phoneNumber="9999999925",
            password="Pass@123",
            type_of_user="is_client",
            is_client=True,
        )
        Tradeorderhistory.objects.create(
            client=assigned_client,
            GroupService="Lite",
            trading_symbol="NIFTY02JUN2623500CE",
            Index_Symbol="NIFTY02JUN2623500CE",
            transaction_type="BUY",
            order_status="completed",
            trade_order_status="OPEN",
            order_id="assigned-open-buy",
            EntryQty=65,
            Entry_Price=100,
        )
        Tradeorderhistory.objects.create(
            client=other_client,
            GroupService="Lite",
            trading_symbol="BANKNIFTY30JUN2653700PE",
            Index_Symbol="BANKNIFTY30JUN2653700PE",
            transaction_type="BUY",
            order_status="completed",
            trade_order_status="OPEN",
            order_id="other-open-buy",
            EntryQty=30,
            Entry_Price=200,
        )

        access_token = str(RefreshToken.for_user(subadmin).access_token)
        response = self.client.get(
            "/api/sl-tp-watcher/scan/",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        client_ids = {item["client_id"] for item in response.data["results"]}
        self.assertIn(assigned_client.id, client_ids)
        self.assertNotIn(other_client.id, client_ids)

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

    def test_subadmin_can_view_assigned_client_broker_activity_only(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        subadmin = User.objects.create_user(
            email="broker-activity-subadmin@example.com",
            firstName="Broker",
            lastName="Subadmin",
            phoneNumber="9999999908",
            password="Pass@123",
            role=subadmin_role,
        )
        assigned_client = User.objects.create_user(
            email="broker-activity-client@example.com",
            firstName="Assigned",
            lastName="Client",
            phoneNumber="9999999907",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
            assigned_client=subadmin,
        )
        unassigned_client = User.objects.create_user(
            email="broker-activity-other@example.com",
            firstName="Other",
            lastName="Client",
            phoneNumber="9999999906",
            password="Pass@123",
            type_of_user="is_client",
            is_client="True",
        )
        access_token = str(RefreshToken.for_user(subadmin).access_token)

        allowed_response = self.client.get(
            f"/api/broker-log-activity/{assigned_client.id}/",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        denied_response = self.client.get(
            f"/api/broker-log-activity/{unassigned_client.id}/",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(allowed_response.status_code, 200)
        self.assertEqual(denied_response.status_code, 403)

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

    @mock.patch("main.tasks.process_single_webhook_trade_task.apply_async")
    def test_webhook_dispatch_queues_each_matched_trade(self, mock_apply_async):
        mock_apply_async.side_effect = [
            SimpleNamespace(id="task-one"),
            SimpleNamespace(id="task-two"),
        ]
        first_trade = ClientTradeSetting.objects.create(
            client=self.client_user,
            symbol="NIFTY",
            product_type="NRML",
        )
        second_trade = ClientTradeSetting.objects.create(
            client=self.other_client,
            symbol="BANKNIFTY",
            product_type="NRML",
        )

        result = process_webhook_signal_task.run(
            trade_ids=[first_trade.pk, second_trade.pk],
            context={"signal_log_id": 123},
            history_mode="default",
        )

        self.assertEqual(result["summary"]["total"], 2)
        self.assertEqual(result["summary"]["queued"], 2)
        self.assertEqual(mock_apply_async.call_count, 2)
        self.assertEqual(
            mock_apply_async.call_args_list[0].kwargs["kwargs"]["trade_id"],
            first_trade.pk,
        )
        self.assertEqual(
            mock_apply_async.call_args_list[0].kwargs["queue"],
            "webhook_execution",
        )
        self.assertEqual(
            mock_apply_async.call_args_list[1].kwargs["kwargs"]["trade_id"],
            second_trade.pk,
        )

    @mock.patch("main.tasks.warm_single_broker_session_task.apply_async")
    def test_broker_login_warmup_uses_dedicated_execution_queue(self, mock_apply_async):
        mock_apply_async.return_value = SimpleNamespace(id="warmup-task")

        task_id = schedule_broker_session_warmup(self.broker_details.pk)

        self.assertEqual(task_id, "warmup-task")
        mock_apply_async.assert_called_once_with(
            kwargs={"broker_details_id": self.broker_details.pk},
            queue="webhook_execution",
        )

    @mock.patch("main.views._process_webhook_trade")
    def test_webhook_single_worker_reloads_trade_setting_before_execution(self, mock_process_trade):
        trade = ClientTradeSetting.objects.create(
            client=self.client_user,
            symbol="NIFTY",
            product_type="NRML",
        )
        ClientTradeSetting.objects.filter(pk=trade.pk).update(product_type="MIS")

        mock_process_trade.return_value = {"status": "success", "trade_setting_id": trade.pk}

        process_single_webhook_trade_task.run(
            trade_id=trade.pk,
            index=1,
            context={"signal_log_id": 123},
            history_mode="default",
        )

        self.assertEqual(mock_process_trade.call_args.args[0].product_type, "MIS")
        self.assertEqual(mock_process_trade.call_args.kwargs["history_id"], f"webhook_123_{self.client_user.pk}_{trade.pk}")

    @mock.patch("main.views._process_webhook_trade", side_effect=RuntimeError("early failure"))
    def test_webhook_single_worker_records_failure_history_on_unhandled_exception(self, mock_process_trade):
        trade = ClientTradeSetting.objects.create(
            client=self.client_user,
            symbol="NIFTY",
            group_service="Lite",
            broker="Alice Blue",
            product_type="MIS",
            quantity=65,
            trade_limit=10,
            is_tread_status=True,
        )
        context = {
            "alert_data": {"symbol": "NIFTY", "signal_time": timezone.now()},
            "symbols": "NIFTY",
            "exch_seg": "NFO",
            "default_price": 24196.75,
            "default_quantity": 65,
            "live_price": 24196.75,
            "transaction_type": "BUY-O",
            "buy_sell": "CE",
            "default_ordertype": "LIMIT",
            "signal_log_id": 456,
        }

        result = process_single_webhook_trade_task.run(
            trade_id=trade.pk,
            index=1,
            context=context,
            history_mode="default",
        )

        expected_history_id = f"webhook_456_{self.client_user.pk}_{trade.pk}"
        history = Tradeorderhistory.objects.get(history_id=expected_history_id)
        self.assertEqual(result["status"], "failed")
        self.assertEqual(history.order_status, "Failed")
        self.assertEqual(history.trade_order_status, "Failed")
        self.assertIn("Webhook worker failed before broker execution", history.failure_reason)

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
    def test_sell_close_webhook_ignores_daily_trade_limit(self, mock_place_order):
        mock_place_order.return_value = {"data": {"status": "complete", "message": "closed"}}
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
            trade_limit=1,
            is_tread_status=True,
            expiry_date=timezone.now(),
        )
        for _ in range(2):
            TradingLog.objects.create(client=self.client_user, symbol="FINNIFTY", strategy="Sparks Lite")
        context = _resolve_webhook_request_context(
            {
                "text": "NIFTY FIN SERVICE",
                "ordertype": "SELL-C",
                "signalprice": "26115.60",
                "stratergyid": "Sparks Lite",
            }
        )

        result = _process_webhook_trade(trade, 0, context, history_id="sell-close-daily-limit")

        self.assertEqual(result["status"], "success")
        self.assertEqual(mock_place_order.call_count, 1)
        close_call = mock_place_order.call_args.args
        self.assertEqual(close_call[4], "SELL")
        self.assertEqual(close_call[30]["transaction_type"], "SELL")

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

    def test_execution_engine_exit_history_uses_matched_open_buy_contract(self):
        from main.execution_engine import ExecutionEngine, ExecutionRequest

        open_history = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY16JUN2623300PE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="completed",
            order_id="open-23300-pe",
            broker="Upstox",
            Entry_type="BUY",
            EntryQty=65,
            Entry_Price=Decimal("115.10"),
            order_params={"symbol": "NIFTY", "strike": 23300, "option_type": "PE", "product_type": "NRML"},
        )
        request = ExecutionRequest(
            LivePrice=Decimal("108.65"),
            group_service="Lite",
            trade=SimpleNamespace(broker="Upstox"),
            user=self.client_user,
            transaction_type="SELL",
            symbol="NIFTY",
            quantity=65,
            strategy="Sparks Lite",
            ordertype="LIMIT",
            product_type="INTRADAY",
            price=Decimal("108.65"),
            Lots=1,
            trade_order_status="CLOSE",
            Entry_type=None,
            Exit_type="SELL",
            Entry_price=None,
            Exit_price=None,
            EntryQty=None,
            ExitQty=65,
            webhook_signal={"ordertype": "BUY-C", "signalprice": 23355.20},
            Exchange="NFO",
            Segment="FNO",
            Index_Symbol="NIFTY",
            triggerPrice=0,
            day="16",
            month="JUN",
            year="26",
            fullyear="2026",
            strike=23400,
            option_type="PE",
            order_params={
                "symbol": "NIFTY",
                "group_service": "Lite",
                "strike": 23400,
                "strike_price": 23400,
                "default_price": 23400,
                "option_type": "PE",
                "transaction_type": "SELL",
            },
            history_id="exit-history-display-uses-open-buy",
        )
        engine = ExecutionEngine()

        result = engine._align_exit_request_with_open_position(request)
        engine._finalize_execution(
            request,
            {"data": {"status": "complete", "order_id": "exit-23300-pe", "message": "Order placed."}},
            {},
            None,
            None,
            time.perf_counter(),
        )

        self.assertIsNone(result)
        exit_history = Tradeorderhistory.objects.get(history_id="exit-history-display-uses-open-buy")
        self.assertEqual(exit_history.order_params["strike"], "23300")
        self.assertEqual(exit_history.order_params["strike_price"], "23300")
        self.assertEqual(exit_history.order_params["default_price"], "23300")
        self.assertEqual(exit_history.order_params["signal_strike"], 23400)
        self.assertEqual(exit_history.order_params["matched_open_history_id"], open_history.history_id)
        self.assertEqual(exit_history.order_params["matched_open_order_id"], "open-23300-pe")
        self.assertEqual(exit_history.order_params["matched_open_trading_symbol"], "NIFTY16JUN2623300PE")
        self.assertEqual(exit_history.order_params["product_type"], "NRML")
        self.assertEqual(request.product_type_name, "NRML")

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
                    "filled_quantity": 65,
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

    def test_force_squareoff_skips_open_buy_position_matching(self):
        close_order, open_position, close_error = prepare_close_order_from_open_position(
            self.client_user,
            {
                "symbol": "NIFTY",
                "transaction_type": "SELL",
                "option_type": "CE",
                "quantity": 65,
                "strike": 23600,
                "force_broker_squareoff": True,
                "order_params": {"order_action": "force_kill_switch_exit"},
            },
            "angel one",
        )

        self.assertIsNone(close_error)
        self.assertIsNone(open_position)
        self.assertEqual(close_order["strike"], 23600)
        self.assertTrue(close_order["force_broker_squareoff"])

    def test_kill_switch_exit_requests_use_limit_orders(self):
        trade_history = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY16JUN2623900PE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="open",
            order_status="complete",
            order_id="26061600086435",
            EntryQty=65,
            Entry_Price=Decimal("21.10"),
            order_params={
                "symbol": "NIFTY",
                "strike": 23900,
                "option_type": "PE",
                "product_type": "NRML",
                "day": "16",
                "month": "JUN",
                "year": "26",
                "fullyear": "2026",
                "quantity": 65,
            },
        )

        regular_request = _build_regular_trade_exit_request(trade_history)
        force_request = _build_regular_trade_exit_request(trade_history, force_broker_squareoff=True)

        self.assertEqual(regular_request.order_type_name, "LIMIT")
        self.assertEqual(force_request.order_type_name, "LIMIT")
        self.assertIsNone(regular_request.limit_price)
        self.assertIsNone(force_request.limit_price)
        self.assertEqual(force_request.order_params["order_action"], "force_kill_switch_exit")
        self.assertEqual(regular_request.product_type_name, "NRML")
        self.assertEqual(force_request.product_type_name, "NRML")
        self.assertEqual(force_request.order_params["product_type"], "NRML")

    def test_force_kill_switch_reuses_saved_angel_contract_details(self):
        from main.views import _build_regular_trade_exit_request

        trade_history = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            broker="Angel One",
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY2624200CE14JUL",
            transaction_type="BUY",
            trade_order_status="complete",
            order_status="complete",
            order_id="260710000415114",
            EntryQty=65,
            Entry_Price=Decimal("104.70"),
            response_data={
                "data": {
                    "broker_order": {
                        "tradingsymbol": "NIFTY14JUL2624200CE",
                        "symboltoken": "51379",
                        "producttype": "INTRADAY",
                    }
                }
            },
            order_params={
                "symbol": "NIFTY",
                "strike": 24200,
                "option_type": "CE",
                "product_type": "MIS",
                "day": "14",
                "month": "JUL",
                "year": "26",
                "fullyear": "2026",
                "quantity": 65,
            },
        )

        request = _build_regular_trade_exit_request(trade_history, force_broker_squareoff=True)

        self.assertEqual(request.order_params["symboltoken"], "51379")
        self.assertEqual(request.order_params["broker_tradingsymbol"], "NIFTY14JUL2624200CE")

    def test_angel_force_kill_validation_skips_contract_master_refresh_for_saved_contract(self):
        from main.execution_engine import ExecutionEngine
        from main.views import _build_regular_trade_exit_request

        self.broker_details.isTokenExpired = False
        self.broker_details.access_token_expiry = timezone.now() + timedelta(hours=1)
        self.broker_details.save(update_fields=["isTokenExpired", "access_token_expiry"])
        trade_history = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            broker="Angel One",
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY2624200CE14JUL",
            transaction_type="BUY",
            trade_order_status="complete",
            order_status="complete",
            order_id="260710000415114",
            EntryQty=65,
            Entry_Price=Decimal("104.70"),
            response_data={
                "data": {
                    "broker_order": {
                        "tradingsymbol": "NIFTY14JUL2624200CE",
                        "symboltoken": "51379",
                        "producttype": "INTRADAY",
                    }
                }
            },
            order_params={
                "symbol": "NIFTY",
                "strike": 24200,
                "option_type": "CE",
                "product_type": "MIS",
                "day": "14",
                "month": "JUL",
                "year": "26",
                "fullyear": "2026",
                "quantity": 65,
            },
        )
        request = _build_regular_trade_exit_request(trade_history, force_broker_squareoff=True)
        engine = ExecutionEngine()
        engine._auth_service.ensure_valid_session = mock.Mock(
            return_value={"status": "success", "session": SimpleNamespace(smart_connect=object())}
        )
        engine._ltp_service.get_ltp = mock.Mock(return_value=90.15)
        engine._contract_manager.initialize = mock.Mock(side_effect=AssertionError("contract refresh should be skipped"))

        result = engine._validate_angel_one_request(request)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["contract"].token, "51379")
        self.assertEqual(result["contract"].symbol, "NIFTY14JUL2624200CE")

    def test_zerodha_kill_switch_reconstructs_contract_from_generic_history_symbol(self):
        from main.execution_engine import ExecutionEngine

        trade_history = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            broker="zerodha",
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="OPEN",
            order_id="2071818666588020736",
            EntryQty=65,
            Entry_Price=Decimal("52.90"),
            order_params={
                "symbol": "NIFTY",
                "tradingsymbol": "NIFTY",
                "strike": 23900,
                "option_type": "CE",
                "product_type": "MIS",
                "expiry": "2026-06-30",
                "quantity": 65,
            },
        )

        request = _build_regular_trade_exit_request(trade_history, force_broker_squareoff=True)

        self.assertEqual(request.order_params["tradingsymbol"], "NIFTY26JUN23900CE")
        self.assertEqual(request.order_params["original_broker_order_id"], "2071818666588020736")
        self.assertEqual(ExecutionEngine._resolved_broker_trade_symbol(request), "NIFTY26JUN23900CE")

    def test_zerodha_execution_uses_weekly_symbol_for_seven_july_expiry(self):
        from main.execution_engine import ExecutionEngine

        trade_history = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            broker="zerodha",
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="OPEN",
            order_id="weekly-symbol-regression",
            EntryQty=65,
            Entry_Price=Decimal("67.00"),
            order_params={
                "symbol": "NIFTY",
                "tradingsymbol": "NIFTY",
                "strike": 24400,
                "option_type": "PE",
                "product_type": "MIS",
                "expiry": "2026-07-07",
                "quantity": 65,
            },
        )

        request = _build_regular_trade_exit_request(trade_history, force_broker_squareoff=True)

        self.assertEqual(request.day, "07")
        self.assertEqual(ExecutionEngine._resolved_broker_trade_symbol(request), "NIFTY2670724400PE")

    @mock.patch("main.views.get_execution_engine")
    def test_force_kill_switch_allows_assigned_subadmin_and_client_only(self, mock_engine_factory):
        mock_engine_factory.return_value.execute_order.return_value = {
            "data": {"status": "complete", "message": "Exit placed", "order_id": "exit-order-1"}
        }
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        assigned_subadmin = User.objects.create_user(
            email="kill-assigned-subadmin@example.com",
            firstName="Assigned",
            lastName="Subadmin",
            phoneNumber="9999999811",
            password="Pass@123",
            role=subadmin_role,
        )
        unassigned_subadmin = User.objects.create_user(
            email="kill-unassigned-subadmin@example.com",
            firstName="Unassigned",
            lastName="Subadmin",
            phoneNumber="9999999812",
            password="Pass@123",
            role=subadmin_role,
        )
        self.client_user.assigned_client = assigned_subadmin
        self.client_user.type_of_user = "is_client"
        self.client_user.is_client = "True"
        self.client_user.save(update_fields=["assigned_client", "type_of_user", "is_client"])
        trade = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY16JUN2623900PE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="complete",
            order_id="kill-entry-order",
            history_id="kill-entry-history",
            EntryQty=65,
            Entry_Price=Decimal("21.10"),
            order_params={
                "symbol": "NIFTY",
                "strike": 23900,
                "option_type": "PE",
                "product_type": "MIS",
                "day": "16",
                "month": "JUN",
                "year": "26",
                "fullyear": "2026",
                "quantity": 65,
            },
        )

        for actor in (assigned_subadmin, self.client_user):
            token = str(RefreshToken.for_user(actor).access_token)
            response = self.client.post(
                "/api/superadmin/force-kill-switch/",
                data=json.dumps({"trade_history_ids": [trade.id], "reason": "Scoped exit"}),
                content_type="application/json",
                HTTP_AUTHORIZATION=f"Bearer {token}",
            )
            self.assertEqual(response.status_code, 200, response.data)
            self.assertEqual(response.data["sent_count"], 1)

        unassigned_token = str(RefreshToken.for_user(unassigned_subadmin).access_token)
        denied_response = self.client.post(
            "/api/superadmin/force-kill-switch/",
            data=json.dumps({"trade_history_ids": [trade.id]}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {unassigned_token}",
        )
        self.assertEqual(denied_response.status_code, 207)
        self.assertEqual(denied_response.data["sent_count"], 0)
        self.assertEqual(mock_engine_factory.return_value.execute_order.call_count, 2)

    @mock.patch("main.views.force_kill_switch_trade_task.apply_async")
    def test_async_force_kill_switch_uses_dedicated_queue_for_every_selected_trade(self, mock_apply_async):
        mock_apply_async.side_effect = [
            SimpleNamespace(id="kill-task-1"),
            SimpleNamespace(id="kill-task-2"),
        ]
        self.client_user.type_of_user = "is_client"
        self.client_user.is_client = "True"
        self.client_user.save(update_fields=["type_of_user", "is_client"])
        trades = [
            Tradeorderhistory.objects.create(
                client=self.client_user,
                GroupService="Lite",
                trading_symbol=f"NIFTY16JUN26239{index}0PE",
                Index_Symbol="NIFTY",
                transaction_type="BUY",
                trade_order_status="OPEN",
                order_status="complete",
                order_id=f"kill-entry-order-{index}",
                history_id=f"kill-entry-history-{index}",
                EntryQty=65,
                Entry_Price=Decimal("21.10"),
                order_params={
                    "symbol": "NIFTY",
                    "strike": 23900 + (index * 10),
                    "option_type": "PE",
                    "product_type": "MIS",
                    "day": "16",
                    "month": "JUN",
                    "year": "26",
                    "fullyear": "2026",
                    "quantity": 65,
                },
            )
            for index in range(2)
        ]
        token = str(RefreshToken.for_user(self.client_user).access_token)

        response = self.client.post(
            "/api/superadmin/force-kill-switch/",
            data=json.dumps({
                "trade_history_ids": [trade.id for trade in trades],
                "reason": "Select all active orders",
                "async": True,
            }),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {token}",
        )

        self.assertEqual(response.status_code, 202, response.data)
        self.assertEqual(response.data["queued_count"], 2)
        self.assertEqual(mock_apply_async.call_count, 2)
        for call in mock_apply_async.call_args_list:
            self.assertEqual(call.kwargs["queue"], "kill_switch")
            self.assertEqual(call.kwargs["priority"], 9)

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

    def test_exit_position_matches_open_buy_order_with_broker_order_id(self):
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
            response_data={"filled_quantity": 65},
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

        self.assertIsNone(close_error)
        self.assertEqual(open_position.order_id, "nifty-ce-pending-open")
        self.assertEqual(close_order["transaction_type"], "SELL")
        self.assertEqual(close_order["option_type"], "CE")
        self.assertEqual(close_order["quantity"], 65)

    def test_exit_position_does_not_match_unfilled_open_broker_order(self):
        Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY26JUL24400PE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="OPEN",
            order_id="unfilled-open-buy",
            EntryQty=65,
            Entry_Price=67,
            response_data={"status": "OPEN", "filled_quantity": 0, "pending_quantity": 65},
            order_params={"option_type": "PE", "symbol": "NIFTY", "strike": 24400},
        )

        close_order, open_position, close_error = prepare_close_order_from_open_position(
            self.client_user,
            {
                "symbol": "NIFTY",
                "group_service": "Lite",
                "transaction_type": "SELL",
                "option_type": "PE",
                "quantity": 65,
            },
            "zerodha",
        )

        self.assertIsNone(open_position)
        self.assertEqual(close_order["transaction_type"], "SELL")
        self.assertIn("No open BUY PE position", close_error["data"]["message"])

    def test_exit_position_does_not_match_open_buy_without_broker_order_id(self):
        Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY26JUN23700CE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="OPEN",
            order_id=None,
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
        self.broker_details.refresh_from_db()
        self.assertIsNone(self.node.assigned_client_id)
        self.assertIsNone(self.broker_details.execution_node_id)

    def test_release_node_clears_stale_broker_level_assignments(self):
        stale_node = ExecutionNode.objects.create(
            name="Stale Broker Node",
            ip_address="10.0.0.30",
            provider="aws",
            server_url="https://stale-node.example.com",
            node_id="stale-node",
        )
        self.broker_details.execution_node = stale_node
        self.broker_details.save(update_fields=["execution_node"])
        assign_execution_node_to_client(self.client_user, self.node)

        release_execution_node(self.client_user)

        self.broker_details.refresh_from_db()
        self.node.refresh_from_db()
        stale_node.refresh_from_db()
        self.assertIsNone(self.node.assigned_client_id)
        self.assertIsNone(self.broker_details.execution_node_id)

    def test_one_node_can_be_assigned_to_multiple_clients(self):
        assign_execution_node_to_client(self.client_user, self.node)
        other_broker_details = ClientBrokerdetails.objects.create(
            client=self.other_client,
            broker_name=self.broker,
            broker_API_KEY="key-2",
            broker_Demate_User_Name="A2",
        )

        assign_execution_node_to_client(self.other_client, self.node)

        self.assertEqual(
            set(ExecutionNodeAssignment.objects.filter(execution_node=self.node).values_list("client_id", flat=True)),
            {self.client_user.id, self.other_client.id},
        )
        self.broker_details.refresh_from_db()
        other_broker_details.refresh_from_db()
        self.assertEqual(self.broker_details.execution_node_id, self.node.id)
        self.assertEqual(other_broker_details.execution_node_id, self.node.id)

    def test_block_order_without_verified_node(self):
        assign_execution_node_to_client(self.client_user, self.node)
        self.node.is_verified_with_broker = False
        self.node.save(update_fields=["is_verified_with_broker"])
        self.broker_details.refresh_from_db()
        with self.assertRaises(ValidationError):
            route_order_to_execution_node(self.client_user, self.broker_details, {"symbol": "NIFTY", "quantity": 1})

    def test_valid_token_marks_verified_proxy_node_from_stale_broker_flag(self):
        proxy_node = ExecutionNode.objects.create(
            name="Verified Proxy With Stale Broker Flag",
            ip_address="10.0.0.41",
            provider="proxy",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=False,
            status=ExecutionNode.STATUS_FREE,
        )
        assign_execution_node_to_client(self.client_user, proxy_node)
        self.broker_details.refresh_from_db()
        self.broker_details.set_session_tokens(
            access_token="active-token",
            expiry=timezone.now() + timedelta(hours=6),
            mark_token_created=True,
        )
        self.broker_details.save()

        marked = mark_execution_node_broker_verified_from_valid_token(self.client_user, proxy_node)

        proxy_node.refresh_from_db()
        self.assertTrue(marked)
        self.assertTrue(proxy_node.is_verified_with_broker)

    def test_expired_token_does_not_mark_verified_proxy_node(self):
        proxy_node = ExecutionNode.objects.create(
            name="Expired Token Proxy",
            ip_address="10.0.0.42",
            provider="proxy",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=False,
            status=ExecutionNode.STATUS_FREE,
        )
        assign_execution_node_to_client(self.client_user, proxy_node)
        self.broker_details.refresh_from_db()
        self.broker_details.set_session_tokens(
            access_token="expired-token",
            expiry=timezone.now() - timedelta(minutes=1),
            mark_token_created=True,
        )
        self.broker_details.save()

        marked = mark_execution_node_broker_verified_from_valid_token(self.client_user, proxy_node)

        proxy_node.refresh_from_db()
        self.broker_details.refresh_from_db()
        self.assertFalse(marked)
        self.assertFalse(proxy_node.is_verified_with_broker)
        self.assertTrue(self.broker_details.isTokenExpired)

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

    def test_superadmin_can_search_assignable_ip_clients_after_release(self):
        superadmin = User.objects.create_user(
            email="superadmin-assignable-ip-pool@example.com",
            firstName="Super",
            lastName="Admin",
            phoneNumber="9999999993",
            password="Pass@123",
            is_superuser=True,
        )
        released_client = User.objects.create_user(
            email="zerodha@yopmail.com",
            firstName="Zerodha",
            lastName="Released",
            phoneNumber="9999999992",
            password="Pass@123",
        )
        client_role, _ = Role.objects.get_or_create(name="Client", defaults={"status": Role.ACTIVE})
        released_client.role = client_role
        released_client.save(update_fields=["role"])
        released_node = ExecutionNode.objects.create(
            name="Released Node",
            ip_address="10.0.0.21",
            assigned_client=released_client,
            status=ExecutionNode.STATUS_ASSIGNED,
        )
        ClientBrokerdetails.objects.create(client=released_client, broker_name=self.broker, execution_node=released_node)
        release_execution_node(released_client)
        assigned_client = User.objects.create_user(
            email="assigned-ip-client@example.com",
            firstName="Assigned",
            lastName="Client",
            phoneNumber="9999999991",
            password="Pass@123",
            is_client=True,
            type_of_user="is_client",
        )
        assigned_node = ExecutionNode.objects.create(
            name="Assigned Node",
            ip_address="10.0.0.20",
            assigned_client=assigned_client,
            status=ExecutionNode.STATUS_ASSIGNED,
        )
        access_token = str(RefreshToken.for_user(superadmin).access_token)

        response = self.client.get(
            "/api/execution-nodes/assignable-clients/?q=zerodha",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )

        self.assertEqual(response.status_code, 200)
        results = response.json()["results"]
        self.assertEqual([item["email"] for item in results], ["zerodha@yopmail.com"])
        self.assertFalse(results[0]["has_execution_node"])

        assigned_response = self.client.get(
            "/api/execution-nodes/assignable-clients/?q=assigned-ip-client",
            HTTP_AUTHORIZATION=f"Bearer {access_token}",
        )
        assigned_results = assigned_response.json()["results"]
        self.assertEqual(assigned_results[0]["execution_node_id"], assigned_node.id)
        self.assertTrue(assigned_results[0]["has_execution_node"])

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

    def test_only_superadmin_can_delete_support_chat(self):
        subadmin_role, _ = Role.objects.get_or_create(name="Sub-Admin", defaults={"status": "active"})
        subadmin = User.objects.create_user(
            email="chat-delete-subadmin@example.com",
            firstName="Delete",
            lastName="Subadmin",
            phoneNumber="9999999111",
            password="Pass@123",
            role=subadmin_role,
        )
        thread = ChatThread.objects.create(client=self.client_user, assigned_subadmin=subadmin, subject="Delete access")
        ChatMessage.objects.create(thread=thread, sender=self.client_user, sender_role=ChatMessage.SENDER_CLIENT, message="Delete me")

        subadmin_token = str(RefreshToken.for_user(subadmin).access_token)
        denied_response = self.client.delete(
            f"/api/support-chat/threads/{thread.id}/",
            HTTP_AUTHORIZATION=f"Bearer {subadmin_token}",
        )
        self.assertEqual(denied_response.status_code, 403)
        self.assertTrue(ChatThread.objects.filter(id=thread.id).exists())

        superadmin = User.objects.create_user(
            email="chat-delete-superadmin@example.com",
            firstName="Delete",
            lastName="Superadmin",
            phoneNumber="9999999112",
            password="Pass@123",
            is_superuser=True,
        )
        superadmin_token = str(RefreshToken.for_user(superadmin).access_token)
        deleted_response = self.client.delete(
            f"/api/support-chat/threads/{thread.id}/",
            HTTP_AUTHORIZATION=f"Bearer {superadmin_token}",
        )
        self.assertEqual(deleted_response.status_code, 204)
        self.assertFalse(ChatThread.objects.filter(id=thread.id).exists())
        self.assertFalse(ChatMessage.objects.filter(thread_id=thread.id).exists())

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

    def test_alice_blue_nested_rejection_message_overrides_top_level_success(self):
        from main.Alice_Blue_Api import _extract_alice_response_message

        message = _extract_alice_response_message({
            "result": [{
                "status": "EC092",
                "message": "Invalid parameter: product should be INTRADAY, LONGTERM or MTF.",
                "brokerOrderId": "",
            }],
            "status": "Ok",
            "message": "Success",
        })

        self.assertIn("Invalid parameter", message)

    def test_alice_blue_a3_product_maps_nrml_to_longterm(self):
        from main.Alice_Blue_Api import _alice_a3_product

        self.assertEqual(_alice_a3_product("MIS"), "INTRADAY")
        self.assertEqual(_alice_a3_product("NRML"), "LONGTERM")
        self.assertEqual(_alice_a3_product("CNC"), "LONGTERM")
        self.assertEqual(_alice_a3_product("MTF"), "MTF")

    def test_alice_blue_pre_placement_errors_are_failed(self):
        from main.Alice_Blue_Api import _alice_failed_response

        response = _alice_failed_response("Invalid LTP")

        self.assertEqual(response["data"]["status"], "Failed")
        self.assertEqual(response["data"]["message"], "Invalid LTP")

    @mock.patch("main.Alice_Blue_Api.get_alice_saved_session")
    @mock.patch("main.Alice_Blue_Api.fetch_instrument_data")
    @mock.patch("main.Alice_Blue_Api._alice_a3_request")
    def test_alice_blue_empty_success_result_is_not_reported_as_success(self, mock_request, mock_fetch, mock_session):
        from main.Alice_Blue_Api import place_alice_orders

        alice = SimpleNamespace(
            alice_session_id="alice-session",
            get_instrument_by_symbol=lambda exchange, symbol: SimpleNamespace(token="51375"),
            get_scrip_info=lambda instrument: {"LTP": 120.25},
        )
        mock_session.return_value = (alice, None)
        mock_request.return_value = {"result": [], "status": "Ok", "message": "Success", "http_status_code": 200}

        response = place_alice_orders(
            LivePrice=0,
            group_service="Sparks Pro",
            api_skey="api-key",
            api_uid="2701394",
            trading_symbol_aliceblue="NIFTY14JUL26P24200",
            transaction_type="BUY",
            symbol="NIFTY",
            quantity=65,
            strategy=None,
            order_type="LIMIT",
            product_type="MIS",
            price=None,
            user=self.client_user,
            Lots=1,
            trade_order_status=None,
            Entry_type=None,
            Exit_type=None,
            Entry_price=None,
            Exit_price=None,
            EntryQty=None,
            ExitQty=None,
            webhook_signal={},
            Exchange="NFO",
            Segment="FNO",
            Index_Symbol="NIFTY",
            history_id="alice-empty-result",
            proxy_config={"https": "http://proxy.example.com:8080"},
            session_id="alice-session",
        )

        self.assertEqual(response["data"]["status"], "Failed")
        self.assertIn("did not provide a broker order id", response["data"]["message"])

    @mock.patch("main.Alice_Blue_Api.get_alice_saved_session")
    @mock.patch("main.Alice_Blue_Api.fetch_instrument_data")
    @mock.patch("main.Alice_Blue_Api._alice_a3_request")
    def test_alice_blue_empty_success_result_recovers_order_id_from_orderbook(
        self,
        mock_request,
        mock_fetch,
        mock_session,
    ):
        from main.Alice_Blue_Api import place_alice_orders

        alice = SimpleNamespace(
            alice_session_id="alice-session",
            get_instrument_by_symbol=lambda exchange, symbol: SimpleNamespace(token="51375"),
            get_scrip_info=lambda instrument: {"LTP": 120.25},
        )
        mock_session.return_value = (alice, None)
        mock_request.side_effect = [
            {"result": [], "status": "Ok", "message": "Success", "http_status_code": 200},
            {
                "status": "Ok",
                "result": [
                    {
                        "orderTag": "alice-empty-result",
                        "brokerOrderId": "26071000060175",
                        "status": "open",
                    }
                ],
            },
        ]

        response = place_alice_orders(
            LivePrice=0,
            group_service="Sparks Pro",
            api_skey="api-key",
            api_uid="2701394",
            trading_symbol_aliceblue="NIFTY14JUL26P24200",
            transaction_type="BUY",
            symbol="NIFTY",
            quantity=65,
            strategy=None,
            order_type="LIMIT",
            product_type="MIS",
            price=None,
            user=self.client_user,
            Lots=1,
            trade_order_status=None,
            Entry_type=None,
            Exit_type=None,
            Entry_price=None,
            Exit_price=None,
            EntryQty=None,
            ExitQty=None,
            webhook_signal={},
            Exchange="NFO",
            Segment="FNO",
            Index_Symbol="NIFTY",
            history_id="alice-empty-result",
            proxy_config={"https": "http://proxy.example.com:8080"},
            session_id="alice-session",
        )

        self.assertEqual(response["data"]["status"], "open")
        self.assertEqual(response["data"]["order_id"], "26071000060175")
        self.assertTrue(response["data"]["response"]["reconciled_from_orderbook"])

    def test_execution_engine_normalizes_nested_error_status_to_failed(self):
        from main.execution_engine import ExecutionEngine

        normalized = ExecutionEngine()._normalize_response({"data": {"status": "error", "message": "Invalid LTP"}, "job_id": 769})

        self.assertEqual(normalized["data"]["status"], "Failed")
        self.assertEqual(normalized["data"]["message"], "Invalid LTP")
        self.assertEqual(normalized["job_id"], 769)

    def test_force_exit_message_prefers_broker_rejection_text(self):
        from main.views import _extract_force_exit_message

        message = _extract_force_exit_message(
            {
                "data": {"status": "Failed", "message": "Success"},
                "meta": {"broker_order": {"text": "RMS: insufficient margin"}},
            }
        )

        self.assertEqual(message, "RMS: insufficient margin")

    def test_sl_tp_snapshot_uses_reference_price_for_open_limit_order(self):
        from main.execution_engine import ExecutionEngine

        request = SimpleNamespace(
            trade=SimpleNamespace(sl_type="POINTS", stop_loss=20, target=30),
            transaction_type="BUY",
            LivePrice=Decimal("847.55"),
        )
        snapshot = ExecutionEngine()._build_sl_tp_snapshot(
            request,
            {},
            {
                "data": {
                    "status": "open",
                    "price": 868.75,
                    "ltp": 847.55,
                    "reference_price": 847.55,
                }
            },
        )

        self.assertEqual(snapshot["entry_reference_price"], 847.55)
        self.assertEqual(snapshot["effective_stop_loss_price"], 827.55)
        self.assertEqual(snapshot["effective_target_price"], 877.55)

    def test_trade_history_open_order_entry_uses_ltp_not_buffered_limit_price(self):
        history = save_trade_order_history(
            Decimal("847.55"),
            "Lite",
            "BUY",
            "OPEN",
            self.client_user,
            "BANKNIFTY",
            "alice-open-847",
            "open",
            {
                "data": {
                    "status": "open",
                    "price": 868.75,
                    "ltp": 847.55,
                    "reference_price": 847.55,
                    "order_id": "alice-open-847",
                }
            },
            "Success",
            "Sparks Lite",
            "LE",
            None,
            None,
            None,
            None,
            None,
            {"ordertype": "SELL-O"},
            "NFO",
            "FNO",
            "BANKNIFTY",
            {"price": 868.75},
            broker="Alice Blue",
            history_id="alice-open-reference-price",
        )

        self.assertEqual(history.Entry_Price, Decimal("847.55"))

    def test_trade_history_completed_order_prefers_average_price(self):
        history = save_trade_order_history(
            Decimal("847.55"),
            "Lite",
            "BUY",
            "OPEN",
            self.client_user,
            "BANKNIFTY",
            "alice-complete-845",
            "complete",
            {
                "data": {
                    "status": "complete",
                    "price": 868.75,
                    "average_price": 845,
                    "ltp": 847.55,
                    "order_id": "alice-complete-845",
                }
            },
            "Success",
            "Sparks Lite",
            "LE",
            None,
            None,
            None,
            None,
            None,
            {"ordertype": "SELL-O"},
            "NFO",
            "FNO",
            "BANKNIFTY",
            {"price": 868.75},
            broker="Alice Blue",
            history_id="alice-complete-average-price",
        )

        self.assertEqual(history.Entry_Price, Decimal("845"))

    def test_trade_history_completed_order_prefers_nested_broker_average_price(self):
        history = save_trade_order_history(
            Decimal("166.80"),
            "Lite",
            "BUY",
            "OPEN",
            self.client_user,
            "NIFTY23JUN2624000CE",
            "angel-complete-167",
            "complete",
            {
                "data": {
                    "status": "complete",
                    "price": 175.0,
                    "executed_price": 175.0,
                    "ltp": 166.8,
                    "reference_price": 166.8,
                    "order_id": "angel-complete-167",
                    "broker_order": {
                        "orderstatus": "complete",
                        "averageprice": 167.05,
                        "filledshares": "65",
                    },
                }
            },
            "Success",
            "Sparks Lite",
            "LE",
            None,
            None,
            None,
            None,
            None,
            {"ordertype": "BUY"},
            "NFO",
            "FNO",
            "NIFTY",
            {"price": 175.0},
            broker="Angel One",
            history_id="angel-complete-nested-average-price",
        )

        self.assertEqual(history.Entry_Price, Decimal("167.05"))
        self.assertEqual(history.EntryQty, 65)

    def test_sl_tp_snapshot_prefers_nested_broker_average_over_buffered_limit(self):
        from main.execution_engine import ExecutionEngine

        request = SimpleNamespace(
            trade=SimpleNamespace(sl_type="POINTS", stop_loss=10, target=15),
            transaction_type="BUY",
            LivePrice=Decimal("166.80"),
        )
        snapshot = ExecutionEngine()._build_sl_tp_snapshot(
            request,
            {"validated_price": 175.0, "ltp": 166.8},
            {
                "data": {
                    "status": "complete",
                    "price": 175.0,
                    "executed_price": 175.0,
                    "ltp": 166.8,
                    "broker_order": {
                        "averageprice": 167.05,
                        "filledshares": "65",
                    },
                }
            },
        )

        self.assertEqual(snapshot["entry_reference_price"], 167.05)
        self.assertEqual(snapshot["effective_stop_loss_price"], 157.05)
        self.assertEqual(snapshot["effective_target_price"], 182.05)

    @mock.patch("main.services.broker_fill_reconciliation.get_broker_adapter")
    def test_broker_fill_refresh_updates_entry_price_and_sltp_thresholds(self, mock_get_adapter):
        from main.services.broker_fill_reconciliation import refresh_trade_fill_from_broker

        trade_setting = ClientTradeSetting.objects.create(
            client=self.client_user,
            group_service="Lite",
            broker="Alice Blue",
            strategy="Sparks Lite",
            symbol="BANKNIFTY",
            quantity=30,
            product_type="INTRADAY",
            is_tread_status=True,
            expiry_date=timezone.now(),
            sl_type="POINTS",
            stop_loss=20,
            target=30,
        )
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            trade_setting=trade_setting,
            GroupService="Lite",
            broker="Alice Blue",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="open",
            order_id="alice-open-847",
            trading_symbol="BANKNIFTY30JUN2655900PE",
            Index_Symbol="BANKNIFTY",
            Entry_Price=Decimal("847.55"),
            EntryQty=30,
            order_params={
                "entry_reference_price": 847.55,
                "effective_stop_loss_price": 827.55,
                "effective_target_price": 877.55,
            },
            sltp_metadata={
                "entry_option_price": 847.55,
                "calculated_stoploss_price": 827.55,
                "calculated_target_price": 877.55,
            },
        )
        adapter = SimpleNamespace(
            get_orderbook=mock.Mock(
                return_value={
                    "status": "success",
                    "response": {
                        "result": [
                            {
                                "brokerOrderId": "alice-open-847",
                                "status": "complete",
                                "averagePrice": "845.00",
                                "filledQuantity": "30",
                            }
                        ]
                    },
                }
            )
        )
        mock_get_adapter.return_value = adapter

        changed = refresh_trade_fill_from_broker(history, self.broker_details)

        self.assertTrue(changed)
        history.refresh_from_db()
        self.assertEqual(history.Entry_Price, Decimal("845.00"))
        self.assertEqual(history.EntryQty, 30)
        self.assertEqual(history.order_status, "complete")
        self.assertEqual(history.order_params["entry_reference_price"], 845.0)
        self.assertEqual(history.order_params["effective_stop_loss_price"], 825.0)
        self.assertEqual(history.order_params["effective_target_price"], 875.0)
        self.assertEqual(history.sltp_metadata["entry_option_price"], 845.0)

    @mock.patch("main.services.broker_fill_reconciliation.get_broker_adapter")
    def test_broker_reconciliation_updates_terminal_status_without_fill_price(self, mock_get_adapter):
        from main.services.broker_fill_reconciliation import refresh_trade_fill_from_broker

        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            broker="Zerodha",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="OPEN",
            order_id="kite-rejected-1",
            trading_symbol="NIFTY26JUN23900CE",
            Index_Symbol="NIFTY",
            EntryQty=65,
        )
        mock_get_adapter.return_value = SimpleNamespace(
            get_orderbook=mock.Mock(
                return_value=[
                    {
                        "order_id": "kite-rejected-1",
                        "status": "REJECTED",
                        "filled_quantity": 0,
                        "average_price": 0,
                        "status_message": "Insufficient funds",
                        "order_timestamp": timezone.now(),
                    }
                ]
            )
        )

        changed = refresh_trade_fill_from_broker(history, self.broker_details)

        self.assertTrue(changed)
        history.refresh_from_db()
        self.assertEqual(history.order_status, "rejected")
        self.assertEqual(history.Entry_status, "rejected")
        self.assertEqual(history.failure_reason, "Insufficient funds")
        self.assertIsInstance(history.response_data["order_timestamp"], str)

    @mock.patch("main.services.broker_fill_reconciliation.get_broker_adapter")
    def test_broker_reconciliation_does_not_mark_rate_limit_as_trade_failure(self, mock_get_adapter):
        from main.services.broker_fill_reconciliation import refresh_trade_fill_from_broker

        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            broker="Angel One",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="pending",
            order_id="angel-rate-limited-1",
            trading_symbol="NIFTY04AUG2624400CE",
            Index_Symbol="NIFTY",
            EntryQty=65,
        )
        mock_get_adapter.return_value = SimpleNamespace(
            get_orderbook=mock.Mock(
                side_effect=ValueError(
                    "Couldn't parse the JSON response received from the server: "
                    "b'Access denied because of exceeding access rate'"
                )
            )
        )

        changed = refresh_trade_fill_from_broker(history, self.broker_details)

        self.assertFalse(changed)
        history.refresh_from_db()
        self.assertEqual(history.order_status, "pending")
        self.assertIsNone(history.failure_reason)

    def test_force_exit_history_saves_without_trade_setting_fk(self):
        from main.execution_engine import ExecutionEngine, ExecutionRequest

        original_history = Tradeorderhistory.objects.create(
            client=self.client_user,
            GroupService="Lite",
            trading_symbol="NIFTY05JUN2623400PE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="completed",
            order_id="alice-open-1",
            broker="Alice Blue",
            Entry_type="LE",
            EntryQty=65,
            Entry_Price=Decimal("100.00"),
        )
        request = ExecutionRequest(
            LivePrice=100,
            group_service="Lite",
            trade=original_history,
            user=self.client_user,
            transaction_type="SELL",
            symbol="NIFTY",
            quantity=65,
            strategy="Sparks Lite",
            ordertype="MARKET",
            product_type="INTRADAY",
            price=None,
            Lots=1,
            trade_order_status="CLOSE",
            Entry_type="LE",
            Exit_type="KILL_SWITCH",
            Entry_price=Decimal("100.00"),
            Exit_price=None,
            EntryQty=65,
            ExitQty=65,
            webhook_signal={"source": "superadmin_force_kill_switch"},
            Exchange="NFO",
            Segment="FNO",
            Index_Symbol="NIFTY",
            triggerPrice=0,
            day="05",
            month="JUN",
            year="26",
            fullyear="2026",
            strike=23400,
            option_type="PE",
            order_params={
                "order_action": "force_kill_switch_exit",
                "original_history_id": original_history.id,
                "force_broker_squareoff": True,
            },
            history_id=f"forcekill_{original_history.id}_test",
        )

        ExecutionEngine()._finalize_execution(
            request,
            {"data": {"status": "Failed", "message": "Broker rejected force exit."}},
            {},
            None,
            None,
            time.perf_counter(),
        )

        exit_history = Tradeorderhistory.objects.get(history_id=f"forcekill_{original_history.id}_test")
        self.assertIsNone(exit_history.trade_setting)
        self.assertEqual(exit_history.failure_reason, "Broker rejected force exit.")
        self.assertEqual(exit_history.order_params["original_history_id"], original_history.id)

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

    @mock.patch("main.broker_instrument_cache.requests.get")
    def test_alice_blue_contract_master_uses_durable_cache(self, mock_get):
        from main.Alice_Blue_Api import ProxyAwareAliceblue

        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        response = mock.Mock()
        response.content = b"Exch,Token,Symbol,Trading Symbol,Expiry Date,Lot Size\n"
        response.raise_for_status.return_value = None
        mock_get.return_value = response
        alice = ProxyAwareAliceblue(user_id="alice-user", api_key="alice-api", proxy_config=proxy_config)

        with tempfile.TemporaryDirectory() as tmpdir, override_settings(BASE_DIR=tmpdir):
            with mock.patch("main.broker_instrument_cache.Path.cwd", return_value=Path(tmpdir)):
                alice.get_contract_master("NFO")

                self.assertTrue((Path(tmpdir) / "main" / "aliceblue_NFO.csv").exists())
                self.assertTrue((Path(tmpdir) / "NFO.csv").exists())

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

    def test_zerodha_trade_symbol_normalizes_midcap_nifty_alias(self):
        symbol = build_trade_symbol(
            {
                "symbol": "MIDCAP NIFTY",
                "day": "28",
                "month": "JUL",
                "year": "26",
                "fullyear": "2026",
                "strike": 14800,
                "option_type": "PE",
            },
            "zerodha",
        )

        self.assertEqual(symbol, "MIDCPNIFTY26JUL14800PE")

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

    @mock.patch("main.zerodha.time.sleep", return_value=None)
    def test_zerodha_order_details_retries_transient_missing_history(self, mock_sleep):
        from main.zerodha import get_order_details

        kite = SimpleNamespace(
            order_history=mock.Mock(
                side_effect=[
                    Exception("Order details not ready"),
                    [],
                    [{"status": "OPEN", "transaction_type": "SELL"}],
                ]
            )
        )

        response = get_order_details("kite-order-open", kite, user=self.client_user)

        self.assertIsInstance(response, list)
        self.assertEqual(response[-1]["status"], "OPEN")
        self.assertEqual(kite.order_history.call_count, 3)
        self.assertEqual(mock_sleep.call_count, 2)

    @mock.patch("main.zerodha.get_live_price")
    @mock.patch("main.zerodha._central_ltp_resolver")
    def test_zerodha_ltp_uses_central_websocket_cache_before_broker_quote(self, mock_resolver, mock_get_live_price):
        from main.zerodha import fetch_zerodha_option_ltp

        mock_resolver.resolve.return_value = SimpleNamespace(instrument_key="NSE_FO|central-123")
        mock_get_live_price.return_value = {
            "instrument_key": "NSE_FO|central-123",
            "ltp": 126.25,
            "is_fresh": True,
            "source": "upstox-websocket",
        }
        kite = SimpleNamespace(ltp=mock.Mock())

        ltp = fetch_zerodha_option_ltp(
            kite,
            "kite-api",
            "kite-access",
            "NFO",
            "NIFTY26JUL24000CE",
            {"https": "http://proxy.example.com:8080"},
            user=self.client_user,
            underlying="NIFTY",
        )

        self.assertEqual(ltp, 126.25)
        kite.ltp.assert_not_called()
        mock_get_live_price.assert_called_once_with(
            instrument_key="NSE_FO|central-123",
            max_age_seconds=5,
        )

    def test_upstox_resolver_parses_zerodha_nifty_weekly_symbol(self):
        parsed = _parse_option_symbol("NIFTY2670724400CE", underlying="NIFTY")

        self.assertEqual(parsed["underlying"], "NIFTY")
        self.assertEqual(parsed["expiry"].strftime("%Y-%m-%d"), "2026-07-07")
        self.assertEqual(parsed["strike"], 24400.0)
        self.assertEqual(parsed["option_type"], "CE")
        self.assertFalse(parsed["month_only"])

    @mock.patch("main.services.upstox_market_data.load_upstox_instruments")
    def test_upstox_resolver_maps_ambiguous_zerodha_monthly_symbol(self, mock_load):
        mock_load.side_effect = lambda exchange: [
            {
                "instrument_key": "NSE_FO|63943",
                "trading_symbol": "NIFTY 24100 CE 28 JUL 26",
                "instrument_type": "CE",
                "underlying_symbol": "NIFTY",
                "expiry": int(
                    timezone.datetime(
                        2026, 7, 28, tzinfo=timezone.get_current_timezone()
                    ).timestamp()
                    * 1000
                ),
                "strike_price": 24100,
                "exchange": "NSE",
            }
        ] if exchange == "NSE" else []

        instrument = UpstoxInstrumentResolver().resolve(
            "NIFTY26JUL24100CE",
            underlying="NIFTY",
        )

        self.assertIsNotNone(instrument)
        self.assertEqual(instrument.instrument_key, "NSE_FO|63943")
        self.assertEqual(instrument.expiry_date.strftime("%Y-%m-%d"), "2026-07-28")

    @mock.patch("main.zerodha.fetch_central_upstox_option_ltp", return_value=121.5)
    @mock.patch("main.zerodha.get_live_price", return_value=None)
    @mock.patch("main.zerodha._central_ltp_resolver")
    def test_zerodha_ltp_uses_single_central_on_demand_quote_before_client_api(
        self,
        mock_resolver,
        _mock_get_live_price,
        mock_central_ltp,
    ):
        from main.zerodha import fetch_zerodha_option_ltp

        instrument = SimpleNamespace(instrument_key="NSE_FO|44654")
        mock_resolver.resolve.return_value = instrument
        kite = SimpleNamespace(ltp=mock.Mock())

        ltp = fetch_zerodha_option_ltp(
            kite,
            "kite-api",
            "kite-access",
            "NFO",
            "NIFTY2670724400CE",
            {"https": "http://proxy.example.com:8080"},
            user=self.client_user,
            underlying="NIFTY",
        )

        self.assertEqual(ltp, 121.5)
        mock_central_ltp.assert_called_once_with(instrument)
        kite.ltp.assert_not_called()

    @mock.patch("main.zerodha.time.sleep", return_value=None)
    def test_zerodha_order_details_polls_open_order_until_terminal(self, mock_sleep):
        from main.zerodha import get_order_details

        kite = SimpleNamespace(
            order_history=mock.Mock(
                side_effect=[
                    [{"status": "OPEN", "transaction_type": "BUY"}],
                    [
                        {"status": "OPEN", "transaction_type": "BUY"},
                        {"status": "COMPLETE", "transaction_type": "BUY"},
                    ],
                ]
            )
        )

        response = get_order_details("kite-order-complete", kite, user=self.client_user)

        self.assertEqual(response[-1]["status"], "COMPLETE")
        self.assertEqual(kite.order_history.call_count, 2)
        mock_sleep.assert_called_once()

    @mock.patch("main.brokers.zerodha.KiteConnect")
    def test_zerodha_adapter_reads_orderbook_through_proxy(self, mock_kite_class):
        zerodha_broker = Broker.objects.create(broker_name="Zerodha", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.other_client,
            broker_name=zerodha_broker,
            broker_API_KEY="kite-api",
            access_token="kite-access",
        )
        mock_kite_class.return_value.orders.return_value = [
            {"order_id": "kite-order-1", "status": "COMPLETE"}
        ]
        proxy_config = {
            "http": "http://proxy.example.com:8080",
            "https": "http://proxy.example.com:8080",
        }

        result = get_broker_adapter(broker_details).get_orderbook(proxy_config=proxy_config)

        self.assertEqual(result[0]["status"], "COMPLETE")
        mock_kite_class.assert_called_once_with(api_key="kite-api", proxies=proxy_config)
        mock_kite_class.return_value.set_access_token.assert_called_once_with("kite-access")

    @mock.patch("main.zerodha.fetch_nse_option_chain_ltp", return_value=10)
    @mock.patch("main.zerodha.requests.get")
    @mock.patch("main.zerodha.KiteConnect")
    def test_zerodha_missing_order_history_is_reconciled_asynchronously(self, mock_kite_class, mock_get, mock_fallback):
        from django.core.cache import cache
        from main.zerodha import place_zerodha_orders

        cache.clear()
        proxy_config = {"http": "http://proxy.example.com:8080", "https": "http://proxy.example.com:8080"}
        kite = mock_kite_class.return_value
        kite.VARIETY_REGULAR = "regular"
        kite.profile.return_value = {"user_id": "kite-user"}
        kite.instruments.return_value = [{"tradingsymbol": "NIFTY26MAY24400CE"}]
        kite.ltp.side_effect = Exception("Insufficient permission for that call.")
        kite.place_order.return_value = "kite-order-no-history"
        kite.order_history.return_value = []
        mock_get.return_value = SimpleNamespace(
            status_code=403,
            content=b"{}",
            json=lambda: {"status": "error", "message": "Insufficient permission for that call."},
        )

        with mock.patch("main.zerodha.time.sleep", return_value=None), mock.patch(
            "main.tasks.reconcile_zerodha_order_task.apply_async"
        ) as mock_reconcile, self.captureOnCommitCallbacks(execute=True):
            response = place_zerodha_orders(
                24087.5, "Lite", "kite-access", "kite-api", "NIFTY26MAY24400CE",
                "SELL", "NIFTY", 65, "strategy", "LIMIT", "MIS", None,
                self.client_user, 1, "LE", None, 10, None, 65, 65, None,
                "NFO", "FNO", "NIFTY", None, "CLOSE", "kite-history-missing",
                proxy_config=proxy_config,
            )

        self.assertEqual(response["data"]["status"], "pending")
        self.assertIn("pending verification", response["data"]["message"])
        history = Tradeorderhistory.objects.get(history_id="kite-history-missing")
        self.assertEqual(history.order_status, "pending")
        self.assertIsNone(history.failure_reason)
        mock_reconcile.assert_called_once_with(kwargs={"trade_history_id": history.id}, countdown=5)

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

    @mock.patch(
        "main.services.external_position_reconciliation.build_requests_proxy_config",
        return_value={"https": "http://proxy.example:8080"},
    )
    @mock.patch("main.services.external_position_reconciliation.get_broker_adapter")
    def test_failed_exit_reconciles_mis_as_angel_intraday(
        self,
        mock_get_adapter,
        _mock_proxy,
    ):
        from main.services.external_position_reconciliation import reconcile_failed_exit_response

        self.broker_details.execution_node = self.node
        self.broker_details.save(update_fields=["execution_node"])
        history = Tradeorderhistory.objects.create(
            client=self.client_user,
            broker="Angel One",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="complete",
            order_id="angel-entry-external-close",
            trading_symbol="NIFTY04AUG2624300CE",
            Index_Symbol="NIFTY",
            Entry_type="BUY",
            Entry_Price=Decimal("102.70"),
            EntryQty=65,
            order_params={"product_type": "MIS"},
        )
        Tradeorderhistory.objects.filter(pk=history.pk).update(
            SignalEntry_time=timezone.now() - timedelta(minutes=5),
        )
        history.refresh_from_db()
        mock_get_adapter.return_value = SimpleNamespace(
            get_positions=mock.Mock(return_value={
                "positions": [{
                    "tradingsymbol": "NIFTY04AUG2624300CE",
                    "producttype": "INTRADAY",
                    "netqty": "0",
                }],
            }),
            get_orderbook=mock.Mock(return_value={
                "orders": [{
                    "orderid": "angel-external-sell",
                    "orderstatus": "complete",
                    "transactiontype": "SELL",
                    "producttype": "INTRADAY",
                    "tradingsymbol": "NIFTY04AUG2624300CE",
                    "filledshares": "65",
                    "averageprice": 105.00,
                    "exchtime": timezone.localtime(timezone.now()).strftime("%d-%b-%Y %H:%M:%S"),
                }],
            }),
        )

        response = reconcile_failed_exit_response(
            history,
            {"data": {"status": "Failed", "message": "Insufficient Funds."}},
        )

        history.refresh_from_db()
        self.assertEqual(response["data"]["status"], "reconciled_closed")
        self.assertEqual(history.trade_order_status, "CLOSE")
        self.assertEqual(history.Exit_Price, Decimal("105.00"))
        self.assertEqual(history.ExitQty, 65)

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

    def test_upstox_fresh_central_price_is_normalized_safely(self):
        self.assertEqual(_positive_number_or_none("92.55"), 92.55)
        self.assertIsNone(_positive_number_or_none(None))
        self.assertIsNone(_positive_number_or_none("invalid"))
        self.assertIsNone(_positive_number_or_none(0))

    @mock.patch("main.upstock.save_trade_order_history")
    @mock.patch("main.upstock.get_order_details")
    def test_upstox_completed_sell_returns_actual_fill_price(self, mock_get_order_details, mock_save_history):
        mock_get_order_details.return_value = {
            "status": "success",
            "data": {
                "status": "complete",
                "order_id": "upstox-exit-1",
                "transaction_type": "SELL",
                "average_price": 86.65,
                "filled_quantity": 130,
                "quantity": 130,
            },
        }

        response = handle_successful_order(
            87.0, "Sparks Pro", "SELL", "upstox-exit-1",
            self.client_user, "NIFTY2680424300CE", "Kill Switch",
            None, "LX", 97.5, None, 130, 130, {},
            "NFO", "FNO", "NIFTY", {"quantity": 130},
            "upstox-access", "CLOSE", "upstox-exit-history",
            proxy_config={"https": "http://proxy.example.com:8080"},
        )

        self.assertEqual(response["data"]["executed_price"], 86.65)
        self.assertEqual(response["data"]["filled_quantity"], 130)
        self.assertEqual(mock_save_history.call_args.args[14], 86.65)

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

    @mock.patch("main.dhanapi.requests.post")
    @mock.patch("main.dhanapi.get_trading_symbol_security_id")
    @mock.patch("main.dhanapi.dhanhq")
    def test_dhan_invalid_token_marks_token_expired_and_failed_history(self, mock_dhan_class, mock_security_lookup, mock_post):
        from main.dhanapi import place_dhan_orders

        dhan_broker = Broker.objects.create(broker_name="Dhan", is_active=True)
        broker_details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=dhan_broker,
            broker_API_UID="dhan-client",
            access_token="bad-token",
            isTokenExpired=False,
        )
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
        dhan.place_order.return_value = {"status": "failure", "remarks": {"error_message": "Invalid Token"}}
        mock_post.return_value = SimpleNamespace(status_code=200, content=b"{}", json=lambda: {"data": {"NSE_FNO": {"12345": {"last_price": 10}}}})
        mock_security_lookup.return_value = {"status": "success", "SECURITY_ID": 12345}

        response = place_dhan_orders(
            "2026-05-12",
            10,
            "Lite",
            "bad-token",
            "dhan-client",
            "NIFTY24400CE",
            "BUY",
            "NIFTY",
            65,
            "strategy",
            "MARKET",
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
            "dhan-invalid-token-history",
            proxy_config=proxy_config,
        )

        self.assertEqual(response["data"]["status"], "Failed")
        self.assertEqual(response["data"]["message"], "Invalid Token")
        broker_details.refresh_from_db()
        self.assertTrue(broker_details.isTokenExpired)
        history = Tradeorderhistory.objects.get(history_id="dhan-invalid-token-history")
        self.assertEqual(history.trade_order_status, "Failed")
        self.assertEqual(history.order_status, "Failed")
        self.assertEqual(history.failure_reason, "Invalid Token")

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
    def test_verify_proxy_public_ip_rejects_rotating_route(self, mock_get):
        node = ExecutionNode.objects.create(
            name="Rotating Proxy Verify",
            ip_address="10.0.0.23",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
        )
        responses = [
            SimpleNamespace(
                status_code=200,
                json=lambda: {"ip": "10.0.0.23"},
                text="10.0.0.23",
                raise_for_status=lambda: None,
            ),
            SimpleNamespace(
                status_code=200,
                json=lambda: {"ip": "10.0.0.24"},
                text="10.0.0.24",
                raise_for_status=lambda: None,
            ),
        ]
        mock_get.side_effect = responses

        result = verify_proxy_public_ip(node)

        node.refresh_from_db()
        self.assertEqual(result["status"], "failed")
        self.assertIn("rotating public IPs", result["message"])
        self.assertFalse(node.proxy_public_ip_verified)

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
            proxy_last_verified_at=timezone.now(),
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

    @mock.patch("main.services.execution_router.verify_proxy_public_ip")
    def test_proxy_order_reverifies_stale_public_ip_before_adapter(self, mock_verify):
        stale_time = timezone.now() - timedelta(minutes=10)
        proxy_node = ExecutionNode.objects.create(
            name="Proxy Stale Route",
            ip_address="10.0.0.24",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            proxy_last_verified_at=stale_time,
            is_verified_with_broker=True,
        )
        assign_execution_node_to_client(self.client_user, proxy_node)
        self.broker_details.execution_node = proxy_node
        self.broker_details.save(update_fields=["execution_node"])
        mock_verify.return_value = {"status": "failed", "message": "Expected 10.0.0.24, got 10.0.0.25."}

        with self.assertRaisesMessage(ValidationError, "Execution proxy public IP changed"):
            route_order_to_execution_node(
                self.client_user,
                self.broker_details,
                {"symbol": "NIFTY", "quantity": 1, "idempotency_key": "proxy-route-stale"},
            )

        proxy_node.refresh_from_db()
        self.assertFalse(proxy_node.is_verified_with_broker)

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
            proxy_last_verified_at=timezone.now(),
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

    @mock.patch("main.angelone.managers.session_manager.SessionManager.validate_session")
    def test_angel_one_token_registration_marks_execution_node_broker_verified(self, mock_validate_session):
        from main.angelone.managers.session_manager import ClientSession
        from main.angelone.services.auth_service import AuthService

        proxy_node = ExecutionNode.objects.create(
            name="Angel Token Proxy",
            ip_address="10.0.0.34",
            execution_type=ExecutionNode.EXECUTION_TYPE_PROXY,
            proxy_host="proxy.example.com",
            proxy_port=8080,
            proxy_protocol=ExecutionNode.PROXY_PROTOCOL_HTTP,
            proxy_public_ip_verified=True,
            is_verified_with_broker=False,
        )
        assign_execution_node_to_client(self.client_user, proxy_node)
        self.broker_details.refresh_from_db()
        session = ClientSession(
            client_id="angel-client",
            api_key="angel-api-key",
            session_key="angel-client:angel-api-key",
            access_token="angel-access",
            refresh_token="angel-refresh",
            feed_token="angel-feed",
            session_expiry=timezone.now() + timedelta(hours=8),
            validated_at=timezone.now(),
        )
        mock_validate_session.return_value = {"status": "success", "session": session}

        result = AuthService().register_existing_tokens(
            client_id="angel-client",
            api_key="angel-api-key",
            access_token="angel-access",
            refresh_token="angel-refresh",
            feed_token="angel-feed",
            broker_details=self.broker_details,
            verify_remote=True,
            proxy_config={"https": "http://proxy.example.com:8080"},
        )

        self.assertEqual(result["status"], "success")
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

    def test_sl_tp_success_statuses_exclude_routed_open_order(self):
        self.assertNotIn("open", SUCCESS_EXIT_STATUSES)

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

    @mock.patch("main.sl_tp_watcher_service.get_live_price")
    def test_sl_tp_payload_status_uses_resolved_instrument_key(self, mock_get_live_price):
        service = SLTPWatcherService()
        service._resolve_market_instrument = mock.Mock(
            return_value=SimpleNamespace(instrument_key="NSE_FO|59079")
        )
        trade_order = SimpleNamespace(
            trading_symbol="BANKNIFTY",
            Index_Symbol="BANKNIFTY2657000CE25AUG",
            sltp_metadata={
                "underlying": "BANKNIFTY",
                "expiry": "2026-08-25",
                "strike": 57000,
                "option_type": "CE",
            },
            order_params={},
        )
        payload = {
            "instrument_key": "NSE_FO|59079",
            "trading_symbol": "BANKNIFTY 57000 CE 25 AUG 26",
            "ltp": 998.1,
            "is_fresh": True,
            "age_seconds": 0.5,
            "underlying": "BANKNIFTY",
            "expiry_date": "2026-08-25",
            "strike": 57000,
            "option_type": "CE",
        }
        mock_get_live_price.side_effect = (
            lambda **kwargs: payload
            if kwargs.get("instrument_key") == "NSE_FO|59079"
            else None
        )

        ltp, price_status, age, subscription_status = service._get_cached_payload_status(trade_order)

        self.assertEqual(ltp, 998.1)
        self.assertIsNone(price_status)
        self.assertEqual(age, 0.5)
        self.assertEqual(subscription_status, "subscribed")

    @mock.patch("main.sl_tp_watcher_service.get_live_price")
    def test_sl_tp_ltp_uses_option_contract_cache_not_plain_underlying_symbol(self, mock_get_live_price):
        service = SLTPWatcherService()
        service._upstox_resolver = SimpleNamespace(
            resolve_contract=mock.Mock(
                return_value=SimpleNamespace(
                    instrument_key="NSE_FO|12345",
                    underlying="NIFTY",
                    expiry_date=timezone.datetime(2026, 6, 2),
                    strike=23500,
                    option_type="PE",
                )
            ),
            resolve=mock.Mock(return_value=None),
        )
        trade_order = SimpleNamespace(
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY2623500PE02JUN",
            order_params={
                "symbol": "NIFTY",
                "expiry": "2026-06-02",
                "strike": 23500,
                "option_type": "PE",
            },
        )
        option_payload = {
            "instrument_key": "NSE_FO|12345",
            "trading_symbol": "NIFTY02JUN2623500PE",
            "ltp": 17.35,
            "is_fresh": True,
            "underlying": "NIFTY",
            "expiry_date": "2026-06-02",
            "strike": 23500,
            "option_type": "PE",
        }

        def live_price_side_effect(**kwargs):
            if kwargs.get("trading_symbol") == "NIFTY":
                return {"ltp": 23517.05, "is_fresh": True, "underlying": "NIFTY"}
            if kwargs.get("instrument_key") == "NSE_FO|12345":
                return None
            if kwargs.get("underlying") == "NIFTY" and kwargs.get("strike") == 23500:
                return option_payload
            return None

        mock_get_live_price.side_effect = live_price_side_effect

        ltp, error = service._get_cached_current_ltp(trade_order)

        self.assertEqual(ltp, 17.35)
        self.assertIsNone(error)
        self.assertNotIn(mock.call(trading_symbol="NIFTY"), mock_get_live_price.mock_calls)

    @mock.patch("main.sl_tp_watcher_service.get_live_price")
    def test_sl_tp_rejects_underlying_ltp_for_option_trade(self, mock_get_live_price):
        service = SLTPWatcherService()
        service._upstox_resolver = SimpleNamespace(
            resolve_contract=mock.Mock(
                return_value=SimpleNamespace(
                    instrument_key="NSE_FO|12345",
                    underlying="NIFTY",
                    expiry_date=timezone.datetime(2026, 6, 2),
                    strike=23500,
                    option_type="PE",
                )
            ),
            resolve=mock.Mock(return_value=None),
        )
        trade_order = SimpleNamespace(
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY2623500PE02JUN",
            order_params={
                "symbol": "NIFTY",
                "expiry": "2026-06-02",
                "strike": 23500,
                "option_type": "PE",
            },
        )
        mock_get_live_price.return_value = {
            "instrument_key": "NSE_INDEX|Nifty 50",
            "trading_symbol": "NIFTY",
            "ltp": 23517.05,
            "is_fresh": True,
            "underlying": "NIFTY",
            "strike": None,
            "option_type": "",
        }

        ltp, error = service._get_cached_current_ltp(trade_order)

        self.assertIsNone(ltp)
        self.assertEqual(error, "Cached live price does not match the option contract.")

    @mock.patch("main.sl_tp_watcher_service.get_ltp", return_value=151.25)
    def test_sl_tp_angel_fallback_uses_resolved_option_symbol_from_metadata(self, mock_get_ltp):
        service = SLTPWatcherService()
        service._get_cached_current_ltp = mock.Mock(return_value=(None, "Option live price is not available in the central cache."))
        contract = SimpleNamespace(token="12345", exchange="NFO", symbol="NIFTY14JUL2624100CE")
        service._contract_manager = SimpleNamespace(
            initialize=mock.Mock(),
            get_contracts_by_symbol=mock.Mock(side_effect=lambda symbol: [contract] if symbol == "NIFTY14JUL2624100CE" else []),
            resolve_option_contract=mock.Mock(return_value=(None, None)),
        )
        trade_order = SimpleNamespace(
            broker="Angel One",
            trading_symbol="NIFTY",
            Index_Symbol="NIFTY",
            Exchange="NFO",
            order_params={
                "symbol": "NIFTY",
                "expiry": "2026-07-14",
                "strike": 24100,
                "option_type": "CE",
            },
            sltp_metadata={
                "underlying": "NIFTY",
                "expiry": "2026-07-14",
                "strike": 24100,
                "option_type": "CE",
                "resolved_trading_symbol": "NIFTY14JUL2624100CE",
            },
        )

        ltp, error = service._get_current_ltp(trade_order, self.broker_details)

        self.assertEqual(ltp, 151.25)
        self.assertIsNone(error)
        service._contract_manager.get_contracts_by_symbol.assert_any_call("NIFTY14JUL2624100CE")
        mock_get_ltp.assert_called_once()

    def test_sl_tp_watcher_uses_broker_ltp_fallback_when_cache_is_missing(self):
        trade_setting = ClientTradeSetting.objects.create(
            client=self.client_user,
            symbol="NIFTY",
            strategy="test",
            broker="Angel One",
            product_type="MIS",
            order_type="LIMIT",
            quantity=50,
            group_service="Test",
            expiry_date=timezone.datetime(2026, 6, 26),
            sl_type="POINTS",
            stop_loss=20,
            target=10,
        )
        trade_order = Tradeorderhistory.objects.create(
            client=self.client_user,
            trade_setting=trade_setting,
            GroupService="Test",
            trading_symbol="NIFTY26JUN24000CE",
            Index_Symbol="NIFTY",
            order_id="entry-1",
            order_status="complete",
            broker="Angel One",
            transaction_type="BUY",
            strategy="test",
            Entry_Price=Decimal("100.00"),
            EntryQty=50,
            Exchange="NFO",
            Segment="FNO",
            Lot=1,
            trade_order_status="OPEN",
            history_id="entry-history-1",
        )
        service = SLTPWatcherService()
        service._get_cached_payload_status = mock.Mock(return_value=(None, "PRICE_MISSING", None, "missing"))
        service._get_current_ltp = mock.Mock(return_value=(111.0, None))
        service._market_is_open_now = mock.Mock(return_value=True)
        service._broker_token_invalid = mock.Mock(return_value=False)
        service._build_exit_request = mock.Mock(return_value=SimpleNamespace(history_id="entry-history-1_sltp_exit"))
        service._execution_engine = SimpleNamespace(
            execute_order=mock.Mock(return_value={"data": {"status": "complete", "message": "Exited"}})
        )

        result = service.process_trade(trade_order)
        trade_order.refresh_from_db()

        self.assertEqual(result.status, "triggered")
        self.assertEqual(result.trigger_reason, "TARGET")
        self.assertEqual(result.subscription_status, "broker_fallback")
        self.assertEqual(trade_order.trade_order_status, "CLOSE")
        service._execution_engine.execute_order.assert_called_once()

    def test_sl_tp_watcher_demo_broker_exit_does_not_require_token(self):
        demo_broker = Broker.objects.create(broker_name="Demo Broker", is_active=True)
        ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=demo_broker,
            isTokenExpired=True,
        )
        trade_setting = ClientTradeSetting.objects.create(
            client=self.client_user,
            symbol="BANKNIFTY",
            strategy="test",
            broker="Demo Broker",
            product_type="MIS",
            order_type="LIMIT",
            quantity=30,
            group_service="DEMO",
            expiry_date=timezone.datetime(2026, 7, 28),
            sl_type="POINTS",
            stop_loss=20,
            target=20,
        )
        trade_order = Tradeorderhistory.objects.create(
            client=self.client_user,
            trade_setting=trade_setting,
            GroupService="DEMO",
            trading_symbol="BANKNIFTY28JUL2658200CE",
            Index_Symbol="BANKNIFTY",
            order_id="DEMO-entry",
            order_status="complete",
            broker="Demo Broker",
            transaction_type="BUY",
            Entry_Price=Decimal("502.10"),
            EntryQty=30,
            Exchange="NFO",
            Segment="FNO",
            Lot=1,
            trade_order_status="OPEN",
            history_id="demo-sltp-entry",
            sltp_metadata={
                "underlying": "BANKNIFTY",
                "expiry": "2026-07-28",
                "strike": 58200,
                "option_type": "CE",
                "calculated_stoploss_price": 482.10,
                "calculated_target_price": 522.10,
            },
        )
        service = SLTPWatcherService()
        service._get_cached_payload_status = mock.Mock(return_value=(478.95, None, 0.0, "live"))
        service._get_current_ltp = mock.Mock(return_value=(478.95, None))
        service._market_is_open_now = mock.Mock(return_value=True)
        service._build_exit_request = mock.Mock(return_value=SimpleNamespace(history_id="demo-sltp-exit"))
        service._execution_engine = SimpleNamespace(
            execute_order=mock.Mock(return_value={"data": {"status": "complete", "message": "Demo exit complete"}})
        )

        result = service.process_trade(trade_order)
        trade_order.refresh_from_db()

        self.assertEqual(result.status, "triggered")
        self.assertEqual(result.trigger_reason, "STOP_LOSS")
        self.assertEqual(trade_order.trade_order_status, "CLOSE")
        self.assertEqual(trade_order.sltp_status, "CLOSED")
        service._execution_engine.execute_order.assert_called_once()

    def test_sl_tp_watcher_demo_broker_exit_does_not_require_broker_details(self):
        trade_setting = ClientTradeSetting.objects.create(
            client=self.other_client,
            symbol="BANKNIFTY",
            strategy="test",
            broker="Demo Broker",
            product_type="MIS",
            order_type="LIMIT",
            quantity=300,
            group_service="DEMO",
            expiry_date=timezone.datetime(2026, 7, 28),
            sl_type="POINTS",
            stop_loss=65,
            target=78,
        )
        trade_order = Tradeorderhistory.objects.create(
            client=self.other_client,
            trade_setting=trade_setting,
            GroupService="DEMO",
            trading_symbol="BANKNIFTY28JUL2656700PE",
            Index_Symbol="BANKNIFTY",
            order_id="DEMO-entry-no-broker-details",
            order_status="complete",
            broker="Demo Broker",
            transaction_type="BUY",
            Entry_Price=Decimal("509.65"),
            EntryQty=300,
            Exchange="NFO",
            Segment="FNO",
            Lot=1,
            trade_order_status="OPEN",
            history_id="demo-sltp-no-broker-details",
            sltp_metadata={
                "underlying": "BANKNIFTY",
                "expiry": "2026-07-28",
                "strike": 56700,
                "option_type": "PE",
                "calculated_stoploss_price": 444.65,
                "calculated_target_price": 587.65,
            },
        )
        service = SLTPWatcherService()
        service._get_cached_payload_status = mock.Mock(return_value=(403.15, None, 0.2, "live"))
        service._get_current_ltp = mock.Mock(return_value=(403.15, None))
        service._market_is_open_now = mock.Mock(return_value=True)
        service._build_exit_request = mock.Mock(return_value=SimpleNamespace(history_id="demo-sltp-no-broker-details-exit"))
        service._execution_engine = SimpleNamespace(
            execute_order=mock.Mock(return_value={"data": {"status": "complete", "message": "Demo exit complete"}})
        )

        result = service.process_trade(trade_order)

        trade_order.refresh_from_db()
        self.assertEqual(result.status, "triggered")
        self.assertEqual(result.trigger_reason, "STOP_LOSS")
        self.assertEqual(trade_order.trade_order_status, "CLOSE")
        self.assertEqual(trade_order.sltp_status, "CLOSED")
        service._execution_engine.execute_order.assert_called_once()

    def test_sl_tp_exit_cooldown_uses_long_pause_for_rate_limit_response(self):
        service = SLTPWatcherService()
        trade_order = SimpleNamespace(history_id="rate-limited-history", id=1)
        response = {
            "data": {
                "status": "Failed",
                "message": "Couldn't parse the JSON response received from the server: b'Access denied because of exceeding access rate'",
                "error_code": "ORDER_EXECUTION_FAILED",
            }
        }

        cooldown_seconds = service._set_exit_cooldown(trade_order, response)
        remaining = service._get_exit_cooldown_remaining(trade_order)

        self.assertEqual(cooldown_seconds, service.RATE_LIMIT_COOLDOWN_SECONDS)
        self.assertIsNotNone(remaining)
        self.assertGreater(remaining, 0)

    def test_sl_tp_exit_cooldown_uses_pause_for_empty_broker_response(self):
        service = SLTPWatcherService()
        trade_order = SimpleNamespace(history_id="empty-response-history", id=1)
        response = {
            "data": {
                "status": "Failed",
                "message": "Angel One returned an empty response while placing the order.",
                "error_code": "EMPTY_BROKER_RESPONSE",
            }
        }

        cooldown_seconds = service._set_exit_cooldown(trade_order, response)

        self.assertEqual(cooldown_seconds, service.EMPTY_RESPONSE_COOLDOWN_SECONDS)

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
        self.assertTrue(_is_public_instrument_master_url("https://v2api.aliceblueonline.com/restpy/static/contract_master/NFO.csv"))
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
