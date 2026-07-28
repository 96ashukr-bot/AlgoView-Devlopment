from decimal import Decimal

from django.test import TestCase

from main.models import Tradeorderhistory, User
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
