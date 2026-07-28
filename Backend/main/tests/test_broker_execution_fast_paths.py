from unittest.mock import Mock, patch

from django.test import SimpleTestCase

from main import dhanapi, groww, upstock


class BrokerExecutionFastPathTests(SimpleTestCase):
    @patch("main.dhanapi.get_live_price")
    def test_dhan_uses_fresh_central_price_before_broker_quote(self, get_live_price):
        get_live_price.return_value = {"ltp": 123.45, "is_fresh": True}
        dhan_client = Mock()

        price = dhanapi.fetch_dhan_option_ltp(
            dhan_client,
            "client",
            "token",
            "NSE_FNO",
            "123",
            {},
            trading_symbol="NIFTY28JUL2624000CE",
            expiry_date="2026-07-28",
            underlying="NIFTY",
        )

        self.assertEqual(price, 123.45)
        dhan_client.get_ltp_data.assert_not_called()

    @patch("main.groww.fetch_groww_option_ltp")
    @patch("main.groww.get_live_price")
    def test_groww_uses_fresh_central_price_before_broker_quote(
        self,
        get_live_price,
        fetch_broker_ltp,
    ):
        get_live_price.return_value = {"ltp": 88.5, "is_fresh": True}

        price = groww.fetch_groww_option_ltp_with_cache(
            "token",
            "NSE",
            "FNO",
            "NIFTY28JUL2624000CE",
            expiry_date="2026-07-28",
            underlying="NIFTY",
            strike=24000,
            option_type="CE",
        )

        self.assertEqual(price, 88.5)
        fetch_broker_ltp.assert_not_called()

    @patch("main.upstock.load_upstox_instruments")
    def test_upstox_lookup_uses_in_memory_index(
        self,
        load_upstox_instruments,
    ):
        upstock._upstox_instrument_indexes.clear()
        load_upstox_instruments.return_value = [{
            "instrument_key": "NSE_FO|123",
            "trading_symbol": "NIFTY28JUL2624000CE",
        }]

        first = upstock.fetch_instrument_details(
            "NIFTY28JUL2624000CE",
            exchange="NSE",
        )
        second = upstock.fetch_instrument_details(
            "NIFTY28JUL2624000CE",
            exchange="NSE",
        )

        self.assertEqual(first["instrument_key"], "NSE_FO|123")
        self.assertEqual(second["instrument_key"], "NSE_FO|123")
        load_upstox_instruments.assert_called_once_with("NSE")
