from django.test import SimpleTestCase
from unittest import mock

from main.brokers.contract_snapshot import (
    SNAPSHOT_KEY,
    build_snapshot,
    canonical_contract_fields,
    immutable_snapshot,
    snapshot_exit_fields,
    valid_snapshot,
)
from main.brokers.zerodha import ZerodhaBroker


class BrokerContractSnapshotTests(SimpleTestCase):
    def test_broker_response_symbol_wins_over_generic_request_symbol(self):
        fields = canonical_contract_fields(
            {"resolved_trading_symbol": "FINNIFTY26SEP26000PE", "instrument_token": 18378242},
            {"original_broker_trading_symbol": "FINNIFTY", "instrument_token": "FINNIFTY"},
        )

        self.assertEqual(fields["original_broker_trading_symbol"], "FINNIFTY26SEP26000PE")
        self.assertEqual(fields["original_broker_instrument_key"], 18378242)

    def test_zerodha_legacy_exit_recovers_exact_live_contract(self):
        adapter = object.__new__(ZerodhaBroker)
        adapter.get_positions = mock.Mock(return_value={"net": [{
            "tradingsymbol": "FINNIFTY26SEP26000PE",
            "instrument_token": 18378242,
            "exchange": "NFO",
            "product": "MIS",
            "quantity": 60,
        }]})

        match = adapter._matching_live_position({
            "original_broker_trading_symbol": "FINNIFTY",
            "symbol": "FINNIFTY",
            "strike": 26000,
            "option_type": "PE",
        }, proxy_config={"https": "http://proxy.example:3128"})

        self.assertEqual(match["tradingsymbol"], "FINNIFTY26SEP26000PE")
        self.assertEqual(match["instrument_token"], 18378242)

    def test_maps_broker_specific_identifiers(self):
        fields = canonical_contract_fields({
            "tradingSymbol": "BANKNIFTY-Aug2026-57600-PE",
            "securityId": "59093",
            "exchangeSegment": "NSE_FNO",
            "productType": "MARGIN",
            "filledQty": 30,
        })

        self.assertEqual(fields["original_broker_security_id"], "59093")
        self.assertEqual(fields["original_broker_trading_symbol"], "BANKNIFTY-Aug2026-57600-PE")
        self.assertEqual(fields["original_broker_product_type"], "MARGIN")

    def test_builds_valid_immutable_dhan_snapshot(self):
        snapshot = build_snapshot(
            broker_name="Dhan",
            fields={
                "original_broker_trading_symbol": "BANKNIFTY-Aug2026-57600-PE",
                "original_broker_security_id": "59093",
                "original_broker_exchange": "NSE_FNO",
                "original_broker_product_type": "MARGIN",
                "original_broker_quantity": 30,
            },
            underlying="BANKNIFTY", expiry="2026-08-25", strike=57600,
            option_type="PE", buy_order_id="buy-1", filled_quantity=30,
        )
        container = {SNAPSHOT_KEY: snapshot}

        self.assertTrue(valid_snapshot(snapshot))
        self.assertEqual(immutable_snapshot(container), snapshot)
        self.assertIsNot(immutable_snapshot(container), snapshot)

    def test_exit_fields_keep_broker_confirmed_identifier_primary(self):
        snapshot = build_snapshot(
            broker_name="Upstox",
            fields={
                "original_broker_trading_symbol": "NIFTY26AUG24200PE",
                "original_broker_instrument_key": "NSE_FO|61670",
                "original_broker_exchange": "NFO",
                "original_broker_product_type": "I",
            },
            underlying="NIFTY", expiry="2026-08-25", strike=24200,
            option_type="PE", buy_order_id="buy-2", filled_quantity=130,
        )

        fields = snapshot_exit_fields(snapshot)

        self.assertEqual(fields["original_broker_instrument_key"], "NSE_FO|61670")
        self.assertEqual(fields["original_broker_trading_symbol"], "NIFTY26AUG24200PE")
        self.assertEqual(fields["original_broker_product_type"], "I")
