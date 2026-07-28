from decimal import Decimal

from django.test import TestCase
from rest_framework.test import APIClient

from main.models import Role, Tradeorderhistory, User
from main.services.eod_mis_closure import close_expired_mis_trades
from main.trade_history_service import consolidate_completed_exit_history
from main.views import _orders_status_filter


class OrdersLifecycleTests(TestCase):
    def setUp(self):
        self.client_user = User.objects.create_user(
            email="orders-lifecycle@example.com",
            firstName="Orders",
            lastName="Lifecycle",
            phoneNumber="9000000001",
            password="Pass@123",
            is_enable=True,
            type_of_user="is_client",
            is_client=True,
        )

    def test_successful_buy_with_populated_exit_quantity_is_active(self):
        trade = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY28JUL2624000CE",
            Index_Symbol="NIFTY28JUL2624000CE",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="COMPLETED",
            order_id="buy-active-1",
            Entry_type="LE",
            Entry_Price=Decimal("100"),
            EntryQty=65,
            ExitQty=0,
        )

        active_ids = Tradeorderhistory.objects.filter(
            _orders_status_filter("ACTIVE")
        ).values_list("id", flat=True)

        self.assertIn(trade.id, active_ids)

    def test_completed_exit_moves_original_buy_to_closed(self):
        buy = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="buy-row-1",
            trading_symbol="NIFTY28JUL2624000CE",
            Index_Symbol="NIFTY28JUL2624000CE",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="COMPLETED",
            order_id="buy-order-1",
            Entry_type="LE",
            Entry_Price=Decimal("100"),
            EntryQty=65,
        )
        exit_row = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="sell-row-1",
            trading_symbol="NIFTY28JUL2624000CE",
            Index_Symbol="NIFTY28JUL2624000CE",
            transaction_type="SELL",
            trade_order_status="CLOSE",
            order_status="COMPLETED",
            order_id="sell-order-1",
            Exit_type="LX",
            Exit_Price=Decimal("110"),
            ExitQty=65,
            order_params={"original_history_id": "buy-row-1"},
        )

        consolidated = consolidate_completed_exit_history(exit_row)
        buy.refresh_from_db()

        self.assertEqual(consolidated.id, buy.id)
        self.assertEqual(buy.trade_order_status, "CLOSE")
        self.assertEqual(buy.Exit_Price, Decimal("110"))
        self.assertEqual(buy.ExitQty, 65)
        self.assertFalse(Tradeorderhistory.objects.filter(pk=exit_row.pk).exists())
        self.assertTrue(
            Tradeorderhistory.objects.filter(
                pk=buy.pk,
            ).filter(_orders_status_filter("CLOSED")).exists()
        )

    def test_failed_order_is_only_in_failed_bucket(self):
        trade = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY28JUL2624000PE",
            transaction_type="BUY",
            trade_order_status="Failed",
            order_status="REJECTED",
            failure_reason="Broker rejected order",
            order_id="failed-order-1",
        )

        self.assertTrue(
            Tradeorderhistory.objects.filter(
                pk=trade.pk,
            ).filter(_orders_status_filter("FAILED")).exists()
        )
        self.assertFalse(
            Tradeorderhistory.objects.filter(
                pk=trade.pk,
            ).filter(_orders_status_filter("ACTIVE")).exists()
        )

    def test_failed_orders_api_includes_rejected_open_history(self):
        admin_role, _ = Role.objects.get_or_create(
            name="Admin",
            defaults={"status": "active"},
        )
        admin = User.objects.create_user(
            email="orders-api-admin@example.com",
            firstName="Orders",
            lastName="Admin",
            phoneNumber="9000000002",
            password="Pass@123",
            role=admin_role,
        )
        trade = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="manual-market-closed-1",
            trading_symbol="NIFTY21JUL2624000CE",
            Index_Symbol="NIFTY",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="Failed",
            failure_reason="Order rejected because the market is outside configured trading hours.",
            broker="Angel One",
            order_id="failed-market-closed-1",
        )
        api_client = APIClient()
        api_client.force_authenticate(admin)

        response = api_client.get("/api/orders/", {"order_bucket": "FAILED"})

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn(trade.id, {item["id"] for item in response.data["results"]})

    def test_orders_filter_options_api_does_not_crash(self):
        admin_role, _ = Role.objects.get_or_create(
            name="Admin",
            defaults={"status": "active"},
        )
        admin = User.objects.create_user(
            email="orders-options-admin@example.com",
            firstName="Orders",
            lastName="Options",
            phoneNumber="9000000003",
            password="Pass@123",
            role=admin_role,
        )
        api_client = APIClient()
        api_client.force_authenticate(admin)

        response = api_client.get("/api/orders/filter-options/")

        self.assertEqual(response.status_code, 200, response.data)
        self.assertIn(
            self.client_user.id,
            {item["id"] for item in response.data["clients"]},
        )

    def test_eod_scan_uses_algoview_client_schema(self):
        result = close_expired_mis_trades(company_id=999, dry_run=True)

        self.assertEqual(result["scanned"], 0)
