from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from main.models import Role, Tradeorderhistory, User
from main.services.eod_mis_closure import close_expired_mis_trades
from main.trade_history_service import (
    consolidate_completed_exit_history,
    resolve_trade_failure_reason,
)
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

    def test_broker_success_aliases_are_active_until_exit(self):
        for index, broker_status in enumerate(
            (
                "OPEN",
                "COMPLETE",
                "COMPLETED",
                "EXECUTED",
                "FILLED",
                "TRADED",
                "SUCCESS",
                "PLACED",
                "TRANSIT",
                "PENDING",
                "PARTIAL",
                "PARTIALLY_FILLED",
            ),
            start=1,
        ):
            with self.subTest(broker_status=broker_status):
                trade = Tradeorderhistory.objects.create(
                    client=self.client_user,
                    trading_symbol=f"NIFTY28JUL2624{index:03d}CE",
                    transaction_type="BUY",
                    trade_order_status="OPEN",
                    order_status=broker_status,
                    order_id=f"active-alias-{index}",
                    Entry_type="LE",
                    Entry_Price=Decimal("100"),
                    EntryQty=65,
                )

                self.assertTrue(
                    Tradeorderhistory.objects.filter(pk=trade.pk)
                    .filter(_orders_status_filter("ACTIVE"))
                    .exists()
                )
                self.assertFalse(
                    Tradeorderhistory.objects.filter(pk=trade.pk)
                    .filter(_orders_status_filter("FAILED"))
                    .exists()
                )
                self.assertFalse(
                    Tradeorderhistory.objects.filter(pk=trade.pk)
                    .filter(_orders_status_filter("CLOSED"))
                    .exists()
                )

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

    def test_closed_trade_status_never_appears_active(self):
        trade = Tradeorderhistory.objects.create(
            client=self.client_user,
            trading_symbol="NIFTY28JUL2624000CE",
            transaction_type="BUY",
            trade_order_status="CLOSE",
            order_status="COMPLETED",
            order_id="already-closed-1",
            Entry_type="LE",
            Entry_Price=Decimal("100"),
            EntryQty=65,
        )

        self.assertFalse(
            Tradeorderhistory.objects.filter(pk=trade.pk)
            .filter(_orders_status_filter("ACTIVE"))
            .exists()
        )
        self.assertTrue(
            Tradeorderhistory.objects.filter(pk=trade.pk)
            .filter(_orders_status_filter("CLOSED"))
            .exists()
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

    def test_failed_status_overrides_open_lifecycle_and_keeps_reason(self):
        reason = "Broker rejected the order."

        self.assertEqual(
            resolve_trade_failure_reason("FAILED", "OPEN", reason),
            reason,
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

    def test_trade_history_returns_one_consolidated_entry_exit_row(self):
        admin_role, _ = Role.objects.get_or_create(
            name="Admin",
            defaults={"status": "active"},
        )
        admin = User.objects.create_user(
            email="one-row-history-admin@example.com",
            firstName="History",
            lastName="Admin",
            phoneNumber="9000000004",
            password="Pass@123",
            role=admin_role,
        )
        parent = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="one-row-buy",
            trading_symbol="NIFTY28JUL2624000CE",
            transaction_type="BUY",
            trade_order_status="CLOSE",
            order_status="COMPLETED",
            order_id="one-row-buy-order",
            Entry_type="LE",
            Entry_Price=Decimal("100"),
            EntryQty=65,
            Exit_type="LX",
            Exit_Price=Decimal("110"),
            ExitQty=65,
            Total=Decimal("650"),
        )
        child_exit = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="one-row-sell",
            trading_symbol="NIFTY28JUL2624000CE",
            transaction_type="SELL",
            trade_order_status="CLOSE",
            order_status="COMPLETED",
            order_id="one-row-sell-order",
            Exit_type="LX",
            Exit_Price=Decimal("110"),
            ExitQty=65,
            order_params={"original_history_id": parent.history_id},
        )
        api_client = APIClient()
        api_client.force_authenticate(admin)

        response = api_client.get("/api/get-trade-history/")

        self.assertEqual(response.status_code, 200, response.data)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(parent.id, result_ids)
        self.assertNotIn(child_exit.id, result_ids)
        parent_payload = next(
            item for item in response.data["results"] if item["id"] == parent.id
        )
        self.assertEqual(Decimal(parent_payload["Entry_Price"]), Decimal("100"))
        self.assertEqual(Decimal(parent_payload["Exit_Price"]), Decimal("110"))
        self.assertEqual(parent_payload["EntryQty"], 65)
        self.assertEqual(parent_payload["ExitQty"], 65)
        self.assertEqual(Decimal(parent_payload["Total"]), Decimal("650"))

    def test_client_trade_history_hides_residual_exit_child_row(self):
        parent = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="client-one-row-buy",
            trading_symbol="NIFTY28JUL2624100CE",
            transaction_type="BUY",
            trade_order_status="CLOSE",
            order_status="COMPLETED",
            order_id="client-one-row-buy-order",
            Entry_type="LE",
            Entry_Price=Decimal("90"),
            EntryQty=65,
            Exit_type="LX",
            Exit_Price=Decimal("95"),
            ExitQty=65,
        )
        child_exit = Tradeorderhistory.objects.create(
            client=self.client_user,
            history_id="client-one-row-sell",
            trading_symbol="NIFTY28JUL2624100CE",
            transaction_type="SELL",
            trade_order_status="CLOSE",
            order_status="COMPLETED",
            order_id="client-one-row-sell-order",
            Exit_type="LX",
            Exit_Price=Decimal("95"),
            ExitQty=65,
            order_params={"original_history_id": parent.history_id},
        )
        api_client = APIClient()
        api_client.force_authenticate(self.client_user)

        response = api_client.get("/api/get-client-trade-history/")

        self.assertEqual(response.status_code, 200, response.data)
        result_ids = {item["id"] for item in response.data["results"]}
        self.assertIn(parent.id, result_ids)
        self.assertNotIn(child_exit.id, result_ids)

    def test_eod_scan_uses_algoview_client_schema(self):
        result = close_expired_mis_trades(company_id=999, dry_run=True)

        self.assertEqual(result["scanned"], 0)

    def test_eod_reconciliation_closes_successful_mis_alias(self):
        trade = Tradeorderhistory.objects.create(
            client=self.client_user,
            date=datetime(2026, 7, 27).date(),
            trading_symbol="NIFTY28JUL2624000CE",
            transaction_type="BUY",
            trade_order_status="complete",
            order_status="complete",
            order_id="stale-mis-success",
            Entry_type="LE",
            Entry_Price=Decimal("100"),
            EntryQty=65,
            LivePrice=Decimal("110"),
            order_params={"product_type": "MIS", "expiry": "2026-07-28"},
        )
        now = timezone.make_aware(datetime(2026, 7, 28, 16, 0))

        result = close_expired_mis_trades(trade_id=trade.id, now=now)
        trade.refresh_from_db()

        self.assertEqual(result["closed"], 1)
        self.assertEqual(trade.trade_order_status, "CLOSE")
        self.assertEqual(trade.Exit_Price, Decimal("110"))
        self.assertEqual(trade.ExitQty, 65)
        self.assertEqual(trade.Total, Decimal("650"))

    def test_eod_reconciliation_closes_expired_nrml_option(self):
        trade = Tradeorderhistory.objects.create(
            client=self.client_user,
            date=datetime(2026, 7, 24).date(),
            trading_symbol="NIFTY28JUL2624000CE",
            transaction_type="BUY",
            trade_order_status="OPEN",
            order_status="EXECUTED",
            order_id="expired-nrml-success",
            Entry_type="LE",
            Entry_Price=Decimal("100"),
            EntryQty=65,
            LivePrice=Decimal("90"),
            order_params={"product_type": "NRML", "expiry": "2026-07-28"},
        )
        now = timezone.make_aware(datetime(2026, 7, 28, 16, 0))

        result = close_expired_mis_trades(trade_id=trade.id, now=now)
        trade.refresh_from_db()

        self.assertEqual(result["closed"], 1)
        self.assertEqual(trade.trade_order_status, "CLOSE")
        self.assertEqual(trade.Exit_Price, Decimal("90"))
        self.assertEqual(trade.Total, Decimal("-650"))

    def test_eod_reconciliation_moves_stale_unconfirmed_order_to_failed(self):
        trade = Tradeorderhistory.objects.create(
            client=self.client_user,
            date=datetime(2026, 7, 27).date(),
            trading_symbol="NIFTY28JUL2624000CE",
            transaction_type="BUY",
            trade_order_status="PROCESSING",
            order_status="Pending",
            Entry_type="LE",
            EntryQty=65,
            order_params={"product_type": "MIS", "expiry": "2026-07-28"},
        )
        now = timezone.make_aware(datetime(2026, 7, 28, 16, 0))

        result = close_expired_mis_trades(trade_id=trade.id, now=now)
        trade.refresh_from_db()

        self.assertEqual(result["failed_unconfirmed"], 1)
        self.assertEqual(trade.trade_order_status, "Failed")
        self.assertEqual(trade.order_status, "Failed")
        self.assertIn("never confirmed", trade.failure_reason)
