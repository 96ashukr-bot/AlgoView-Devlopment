from copy import deepcopy
from datetime import timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase, TestCase
from django.utils import timezone

from main.models import BrokerOrderIntent
from main.services.uncertain_exit_recovery import _open_without_sell, recover_broker_absent_exit, OBSERVATION_KEY
from main.tests.test_webhook_exit_completion import WebhookExitCompletionTests


def fixtures():
    snapshot = {"broker_instrument_id": 12108290, "broker_trading_symbol": "NIFTY2691523500PE", "broker_exchange": "NFO", "broker_product_type": "MIS", "buy_order_id": "BUY-1"}
    order = {"instrument_token": 12108290, "tradingsymbol": "NIFTY2691523500PE", "exchange": "NFO", "product": "MIS", "order_id": "BUY-1", "transaction_type": "BUY", "status": "COMPLETE", "filled_quantity": 65}
    position = {**order, "quantity": 65, "day_buy_quantity": 65, "day_sell_quantity": 0, "overnight_quantity": 0}
    return snapshot, [order], {"net": [position]}


class BrokerAbsenceEvidenceTests(SimpleTestCase):
    def setUp(self):
        self.snapshot, self.orders, self.positions = fixtures()

    def evidence(self):
        return _open_without_sell(self.snapshot, self.orders, self.positions, broker="zerodha", required_quantity=65)

    def test_exact_open_buy_is_proven(self):
        self.assertEqual(self.evidence()["net_quantity"], 65)

    def test_additional_buy_does_not_increase_requested_exit(self):
        self.orders.append({**self.orders[0], "order_id": "BUY-2"})
        self.positions["net"][0].update(quantity=130, day_buy_quantity=130)
        evidence = self.evidence()
        self.assertEqual(evidence["net_quantity"], 130)
        self.assertEqual(evidence["buy_order_id"], "BUY-1")

    def test_any_matching_sell_preserves_duplicate_protection(self):
        for status in ["OPEN", "COMPLETE", "CANCELLED", "REJECTED", "UNKNOWN"]:
            self.orders = [self.orders[0], {**self.orders[0], "order_id": "SELL-1", "transaction_type": "SELL", "status": status}]
            self.assertIsNone(self.evidence())

    def test_missing_buy_or_incomplete_books_cannot_prove_absence(self):
        for orders in [[], None, {"status": "error"}, ["malformed"]]:
            self.assertIsNone(_open_without_sell(self.snapshot, orders, self.positions, broker="zerodha", required_quantity=65))

    def test_flat_partly_sold_or_mismatched_positions_are_not_released(self):
        for changes in [{"quantity": 0}, {"day_sell_quantity": 1}, {"day_buy_quantity": 130}, {"overnight_quantity": 65}, {"instrument_token": 999}, {"product": "NRML"}]:
            positions = deepcopy(self.positions); positions["net"][0].update(changes)
            self.assertIsNone(_open_without_sell(self.snapshot, self.orders, positions, broker="zerodha", required_quantity=65))

    def test_upstox_requires_successful_complete_responses(self):
        orders = {"status": "success", "data": self.orders}
        positions = {"status": "success", "data": self.positions["net"]}
        self.assertIsNotNone(_open_without_sell(self.snapshot, orders, positions, broker="upstox", required_quantity=65))
        orders["status"] = "error"
        self.assertIsNone(_open_without_sell(self.snapshot, orders, positions, broker="upstox", required_quantity=65))


class BrokerAbsenceRecoveryTests(TestCase):
    def setUp(self):
        WebhookExitCompletionTests.setUp(self)
        self.now = timezone.now()
        self.snapshot, self.orders, self.positions = fixtures()
        self.trade.broker = "Zerodha"; self.trade.order_id = "BUY-1"
        self.trade.order_params = {"broker_contract_snapshot": self.snapshot}
        self.trade.save(update_fields=["broker", "order_id", "order_params"])
        self.intent.lifecycle_state = "submission_uncertain"
        self.intent.heartbeat_at = self.now - timedelta(minutes=10)
        self.intent.save(update_fields=["lifecycle_state", "heartbeat_at"])
        self.adapter = Mock()
        self.adapter.get_orderbook.return_value = self.orders
        self.adapter.get_positions.return_value = self.positions
        self.details = SimpleNamespace(execution_node_id=1, execution_node=object())

    def recover(self, offset=0):
        with patch("main.services.uncertain_exit_recovery.timezone.now", return_value=self.now + timedelta(seconds=offset)), patch("main.services.uncertain_exit_recovery._broker_details_for_trade", return_value=self.details), patch("main.services.uncertain_exit_recovery.session_policy_error", return_value=None), patch("main.services.uncertain_exit_recovery.build_requests_proxy_config", return_value={"https": "test-route"}), patch("main.services.uncertain_exit_recovery.get_broker_adapter", return_value=self.adapter):
            result = recover_broker_absent_exit(self.intent.pk)
        self.intent.refresh_from_db()
        return result

    def test_requires_two_separated_observations_and_never_submits(self):
        self.assertEqual(self.recover(), "observing")
        self.assertEqual(self.recover(5), "observing")
        self.assertEqual(self.recover(11), "released")
        self.assertEqual(self.intent.lifecycle_state, "manual_attention")
        self.assertEqual(self.intent.remaining_quantity, 65)
        self.assertEqual(self.intent.requested_quantity, 65)
        self.assertIsNone(self.recover(22))
        self.adapter.place_order.assert_not_called()
        self.assertEqual(BrokerOrderIntent.objects.count(), 1)
        self.trade.refresh_from_db(); self.assertEqual(self.trade.trade_order_status, "OPEN")

    def test_new_sell_between_observations_resets_proof(self):
        self.assertEqual(self.recover(), "observing")
        self.adapter.get_orderbook.return_value = self.orders + [{**self.orders[0], "transaction_type": "SELL", "status": "OPEN"}]
        self.assertIsNone(self.recover(11))
        self.assertEqual(self.intent.lifecycle_state, "submission_uncertain")
        self.assertNotIn(OBSERVATION_KEY, self.intent.outcome)

    def test_network_failure_invalidates_first_observation(self):
        self.assertEqual(self.recover(), "observing")
        self.adapter.get_positions.side_effect = TimeoutError()
        self.assertIsNone(self.recover(11))
        self.assertNotIn(OBSERVATION_KEY, self.intent.outcome)

    def test_stale_observation_requires_a_new_pair(self):
        self.assertEqual(self.recover(), "observing")
        self.assertEqual(self.recover(100), "observing")
        self.assertEqual(self.recover(111), "released")

    def test_accepted_and_recent_exits_are_never_released(self):
        self.intent.lifecycle_state = "broker_accepted"; self.intent.save(update_fields=["lifecycle_state"])
        self.assertIsNone(self.recover())
        self.intent.lifecycle_state = "submission_uncertain"; self.intent.heartbeat_at = self.now
        self.intent.save(update_fields=["lifecycle_state", "heartbeat_at"])
        self.assertIsNone(self.recover())
        self.adapter.get_orderbook.assert_not_called()

    def test_concurrent_acceptance_cannot_be_overwritten(self):
        self.assertEqual(self.recover(), "observing")
        def accept(**kwargs):
            BrokerOrderIntent.objects.filter(pk=self.intent.pk).update(lifecycle_state="broker_accepted", broker_order_id="SELL-1")
            return self.positions
        self.adapter.get_positions.side_effect = accept
        self.assertIsNone(self.recover(11))
        self.assertEqual(self.intent.lifecycle_state, "broker_accepted")

    def test_prior_day_intent_cannot_use_today_orderbook(self):
        BrokerOrderIntent.objects.filter(pk=self.intent.pk).update(created_at=self.now-timedelta(days=1))
        self.assertIsNone(self.recover())
        self.adapter.get_orderbook.assert_not_called()
