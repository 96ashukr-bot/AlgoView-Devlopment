from types import SimpleNamespace

from django.test import SimpleTestCase

from main.services.broker_fill_reconciliation import find_broker_fill
from main.tasks import _reconciliation_is_terminal


class BrokerSnapshotReconciliationTests(SimpleTestCase):
    def test_aggregated_fill_retains_broker_contract_identity(self):
        match = find_broker_fill(
            {
                "data": [
                    {
                        "orderid": "BUY-123",
                        "status": "complete",
                        "averageprice": "61.85",
                        "filledshares": "130",
                        "tradingsymbol": "NIFTY08SEP2623800PE",
                        "symboltoken": "42632",
                        "exchange": "NFO",
                        "producttype": "CARRYFORWARD",
                    }
                ]
            },
            "BUY-123",
        )

        self.assertEqual(match["record"]["tradingsymbol"], "NIFTY08SEP2623800PE")
        self.assertEqual(match["record"]["symboltoken"], "42632")
        self.assertEqual(match["quantity"], 130)

    def test_completed_buy_without_snapshot_is_not_terminal(self):
        history = SimpleNamespace(
            transaction_type="BUY",
            order_status="complete",
            Entry_Price=61.85,
            Exit_Price=None,
            order_params={},
        )

        self.assertFalse(_reconciliation_is_terminal(history))

    def test_completed_buy_with_valid_snapshot_is_terminal(self):
        history = SimpleNamespace(
            transaction_type="BUY",
            order_status="complete",
            Entry_Price=61.85,
            Exit_Price=None,
            order_params={
                "broker_contract_snapshot": {
                    "schema_version": 1,
                    "broker_trading_symbol": "NIFTY08SEP2623800PE",
                    "broker_instrument_id": "42632",
                    "broker_exchange": "NFO",
                    "broker_product_type": "CARRYFORWARD",
                    "filled_quantity": 130,
                    "buy_order_id": "BUY-123",
                }
            },
        )

        self.assertTrue(_reconciliation_is_terminal(history))
