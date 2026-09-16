from datetime import date, datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest import mock

from django.test import SimpleTestCase

from main.execution_engine import ExecutionEngine
from main.manual_trade_service import _manual_trade_live_price
from main.services.demo_pricing import get_demo_option_premium


class DemoPremiumTests(SimpleTestCase):
    def setUp(self):
        self.contract = dict(underlying="NIFTY", expiry_date=date(2026, 9, 22), strike=23300, option_type="CE")
        self.cache_patch = mock.patch("main.services.demo_pricing.get_live_price", return_value=None)
        self.cache = self.cache_patch.start()
        self.addCleanup(self.cache_patch.stop)
        self.resolver_patch = mock.patch("main.services.upstox_market_data.get_upstox_instrument_resolver")
        self.resolver = self.resolver_patch.start().return_value
        self.addCleanup(self.resolver_patch.stop)
        self.quote_patch = mock.patch("main.services.upstox_market_data.fetch_central_upstox_option_ltp", return_value=None)
        self.quote = self.quote_patch.start()
        self.addCleanup(self.quote_patch.stop)

    def test_fresh_premium_is_used_without_rest(self):
        self.cache.return_value = {"is_fresh": True, "ltp": 156.2}
        self.assertEqual(get_demo_option_premium(**self.contract), 156.2)
        self.quote.assert_not_called()

    def test_stale_quote_fetches_exact_expiry_strike_and_side(self):
        self.cache.return_value = {"is_fresh": False, "ltp": 140}
        self.quote.return_value = 156.2
        self.assertEqual(get_demo_option_premium(**self.contract), 156.2)
        self.resolver.resolve_contract.assert_called_once_with(
            underlying="NIFTY", expiry_date="2026-09-22", strike=23300, option_type="CE")
        self.quote.assert_called_once_with(self.resolver.resolve_contract.return_value)

    def test_missing_contract_does_not_guess_another_expiry(self):
        self.resolver.resolve_contract.return_value = None
        self.assertIsNone(get_demo_option_premium(**self.contract))
        self.quote.assert_not_called()

    def test_missing_expiry_fails_closed(self):
        self.assertIsNone(get_demo_option_premium(**{**self.contract, "expiry_date": None}))
        self.cache.assert_not_called()

    def test_invalid_quotes_cannot_be_fills(self):
        for value in (None, 0, -1, "NaN", "Infinity", "bad"):
            with self.subTest(value=value):
                self.cache.return_value = {"is_fresh": True, "ltp": value}
                self.quote.return_value = value
                self.assertIsNone(get_demo_option_premium(**self.contract))

    def test_market_data_error_fails_closed(self):
        self.quote.side_effect = RuntimeError("unavailable")
        self.assertIsNone(get_demo_option_premium(**self.contract))

    def request(self, side):
        return SimpleNamespace(
            option_type_value="CE", underlying_symbol="NIFTY", strike_value=23300,
            resolved_expiry=datetime(2026, 9, 22), order_params={"manual_trade_price_source": "broker_adapter_live_price"},
            LivePrice=23300, limit_price=23300, Entry_price=23300, Exit_price=23300,
            is_exit_order=side == "SELL", transaction_type=side,
        )

    def test_buy_and_sell_never_fall_back_to_strike_or_entry_price(self):
        engine = ExecutionEngine.__new__(ExecutionEngine)
        for side in ("BUY", "SELL"):
            with self.subTest(side=side):
                self.assertIsNone(engine._demo_fill_price(self.request(side)))

    def test_buy_and_sell_replace_caller_strike_with_market_premium(self):
        self.cache.return_value = {"is_fresh": True, "ltp": 156.2}
        engine = ExecutionEngine.__new__(ExecutionEngine)
        for side in ("BUY", "SELL"):
            with self.subTest(side=side):
                request = self.request(side)
                self.assertEqual(engine._demo_fill_price(request), 156.2)
                self.assertEqual(request.order_params["ltp"], 156.2)

    def test_manual_demo_without_quote_is_rejected(self):
        batch = SimpleNamespace(symbol="NIFTY", strike_price=Decimal("23300"))
        setting = SimpleNamespace(broker="Demo Broker", expiry_date=datetime(2026, 9, 22))
        with self.assertRaisesRegex(ValueError, "Live option premium is unavailable"):
            _manual_trade_live_price(batch, setting, "CE")

    def test_manual_demo_uses_premium(self):
        self.cache.return_value = {"is_fresh": True, "ltp": 156.2}
        batch = SimpleNamespace(symbol="NIFTY", strike_price=Decimal("23300"))
        setting = SimpleNamespace(broker="Demo Broker", expiry_date=datetime(2026, 9, 22))
        self.assertEqual(_manual_trade_live_price(batch, setting, "CE"), (Decimal("156.20"), "demo_live_option_price"))

    @mock.patch("main.manual_trade_service.get_live_price", return_value=None)
    def test_real_broker_adapter_reference_path_is_unchanged(self, cached):
        batch = SimpleNamespace(symbol="NIFTY", strike_price=Decimal("23300"))
        setting = SimpleNamespace(broker="Zerodha", expiry_date=datetime(2026, 9, 22))
        self.assertEqual(_manual_trade_live_price(batch, setting, "CE"), (Decimal("23300.00"), "broker_adapter_live_price"))
        self.quote.assert_not_called()
