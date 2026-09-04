from decimal import Decimal

from django.test import TestCase

from main.models import BrokerOrderIntent, Role, Tradeorderhistory, User
from main.services.exit_dispatch import exit_queue_for_broker
from main.services.exit_intents import (
    bind_webhook_intent_to_buy,
    record_fill,
    reconcile_intent_from_trade,
    reserve_exit_intent,
)
from main.services.order_streams import create_intent


class UnifiedExitIntentTests(TestCase):
    def setUp(self):
        role = Role.objects.create(name="exit-intent-test")
        self.client = User.objects.create_user(
            email="exit-intent@example.test", firstName="Exit", lastName="Client",
            phoneNumber="9000000991", password="test", role=role, is_enable=True,
        )
        self.snapshot = {
            "schema_version": 1, "broker": "Zerodha",
            "broker_trading_symbol": "NIFTY08SEP2624000CE",
            "broker_instrument_id": "NIFTY08SEP2624000CE",
            "broker_exchange": "NFO", "broker_segment": "NFO",
            "broker_exchange_type": None, "broker_product_type": "MIS",
            "filled_quantity": 65, "underlying": "NIFTY",
            "expiry": "2026-09-08", "strike": 24000, "option_type": "CE",
            "buy_order_id": "BUY-1", "created_at": "2026-09-04T09:00:00+05:30",
        }
        self.buy = Tradeorderhistory.objects.create(
            client=self.client, broker="Zerodha", trading_symbol="NIFTY08SEP2624000CE",
            Index_Symbol="NIFTY", transaction_type="BUY", order_status="COMPLETE",
            trade_order_status="OPEN", order_id="BUY-1", EntryQty=65,
            Entry_Price=Decimal("100.00"),
            order_params={"broker_contract_snapshot": self.snapshot},
        )

    def test_all_exit_sources_join_one_exact_buy(self):
        first, created = reserve_exit_intent(
            trade=self.buy, source="sl_tp", source_type="sltp_exit",
            trigger_id="sl-1", publish=False,
        )
        second, duplicate_created = reserve_exit_intent(
            trade=self.buy, source="kill_switch", source_type="kill_switch_exit",
            trigger_id="kill-1", publish=False,
        )
        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.contract_snapshot, self.snapshot)

    def test_webhook_binds_to_exact_buy_and_joins_existing_exit(self):
        existing, _ = reserve_exit_intent(
            trade=self.buy, source="sl_tp", source_type="sltp_exit",
            trigger_id="sl-first", publish=False,
        )
        generic, _ = create_intent(
            idempotency_key="webhook-overlap", kind=BrokerOrderIntent.KIND_EXIT,
            broker="Zerodha", client_id=self.client.id, source_type="webhook_trade",
            source_id="45", payload={}, publish=False,
        )
        joined = bind_webhook_intent_to_buy(generic.id, self.buy, trigger_id="signal-overlap")
        self.assertEqual(joined.id, existing.id)
        generic.refresh_from_db()
        self.assertEqual(generic.lifecycle_state, BrokerOrderIntent.LIFECYCLE_CANCELLED)

    def test_partial_fill_tracks_only_remaining_quantity(self):
        intent, _ = reserve_exit_intent(
            trade=self.buy, source="kill_switch", source_type="kill_switch_exit",
            trigger_id="kill-fill", publish=False,
        )
        record_fill(intent_id=intent.id, quantity=25, price="95", broker_trade_id="F1")
        intent.refresh_from_db()
        self.assertEqual(intent.lifecycle_state, BrokerOrderIntent.LIFECYCLE_PARTIAL)
        self.assertEqual(intent.remaining_quantity, 40)
        record_fill(intent_id=intent.id, quantity=40, price="94", broker_trade_id="F2")
        intent.refresh_from_db()
        self.assertEqual(intent.lifecycle_state, BrokerOrderIntent.LIFECYCLE_FILLED)
        self.assertEqual(intent.remaining_quantity, 0)

    def test_panel_closes_only_after_buy_row_is_reconciled(self):
        intent, _ = reserve_exit_intent(
            trade=self.buy, source="webhook", source_type="webhook_exit_direct",
            trigger_id="webhook-close", publish=False,
        )
        self.assertFalse(reconcile_intent_from_trade(intent.id))
        Tradeorderhistory.objects.filter(pk=self.buy.pk).update(trade_order_status="CLOSE", ExitQty=65)
        self.assertTrue(reconcile_intent_from_trade(intent.id))

    def test_live_broker_without_snapshot_fails_closed(self):
        legacy = Tradeorderhistory.objects.create(
            client=self.client, broker="Zerodha", trading_symbol="NIFTY",
            transaction_type="BUY", order_status="COMPLETE", trade_order_status="OPEN",
            order_id="BUY-MISSING", EntryQty=65, order_params={},
        )
        with self.assertRaisesRegex(ValueError, "broker-confirmed contract snapshot"):
            reserve_exit_intent(
                trade=legacy, source="kill_switch", source_type="kill_switch_exit",
                trigger_id="unsafe", publish=False,
            )

    def test_brokers_have_isolated_exit_queues(self):
        self.assertEqual(exit_queue_for_broker("Angel One"), "exit_angelone")
        self.assertEqual(exit_queue_for_broker("5Paisa"), "exit_5paisa")
        self.assertNotEqual(exit_queue_for_broker("Dhan"), exit_queue_for_broker("Zerodha"))
