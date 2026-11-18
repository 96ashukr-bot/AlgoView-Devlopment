from types import SimpleNamespace
from unittest.mock import patch
from django.test import SimpleTestCase
from main.brokers.zerodha import ZerodhaBroker
from main.services.zerodha_instruments import resolve_zerodha_option_contract

class ZerodhaNFOContractTests(SimpleTestCase):
    def setUp(self):
        self.order={'symbol':'NIFTY','strike':25200,'option_type':'PE','expiry':'2026-11-23',
                    'quantity':650,'transaction_type':'BUY','Exchange':'NFO','order_type':'MARKET'}
        self.row={'name':'NIFTY','strike':25200,'instrument_type':'PE','expiry':'2026-11-23',
                  'tradingsymbol':'NIFTY26NOV25200PE','instrument_token':16499714,'exchange':'NFO','lot_size':65}
        self.master=patch('main.services.zerodha_instruments.load_zerodha_instrument_index',return_value={'contract':self.row}).start()
        self.addCleanup(patch.stopall)

    def submit(self,order):
        broker=ZerodhaBroker(SimpleNamespace(client=SimpleNamespace(id=1),access_token='test',broker_API_KEY='test'))
        with patch.object(broker,'daily_session_error',return_value=None),patch('main.brokers.zerodha.prepare_close_order_from_open_position',return_value=(order,None,None)),patch('main.brokers.zerodha.mark_open_position_closed'),patch('main.brokers.zerodha.place_zerodha_orders',return_value={'data':{'status':'open'}}) as place:
            return broker.place_order({'order':order},proxy_config={'https':'http://proxy.invalid'}),place

    def test_holiday_monthly_expiry_resolves_from_master(self):
        self.assertEqual(resolve_zerodha_option_contract(self.order)['tradingsymbol'],'NIFTY26NOV25200PE')

    def test_market_and_limit_submit_exact_listed_symbol_and_client_proxy(self):
        for kind in ['MARKET','LIMIT']:
            result,place=self.submit({**self.order,'order_type':kind,'trade_symbol':'NIFTY26N2325200PE'})
            self.assertEqual(place.call_args.args[4],'NIFTY26NOV25200PE')
            self.assertEqual(place.call_args.kwargs['proxy_config'],{'https':'http://proxy.invalid'})
            self.assertEqual(result['data']['instrument_token'],16499714)

    def test_missing_and_conflicting_expiries_block_submission(self):
        for change in [{'expiry':'2026-11-24'},{'strike':25300},{'option_type':'CE'},{'order_params':{'expiry':'2026-11-24'}}]:
            result,place=self.submit({**self.order,**change})
            self.assertEqual(result['data']['error_code'],'INSTRUMENT_CONTRACT_MISMATCH')
            place.assert_not_called()

    def test_existing_sell_contract_is_not_resolved_again(self):
        result,place=self.submit({**self.order,'transaction_type':'SELL','trade_symbol':'NIFTY26NOV25200PE'})
        self.master.assert_not_called()
        self.assertEqual(place.call_args.args[4],'NIFTY26NOV25200PE')

    def test_unrelated_cash_orders_keep_existing_path(self):
        result,place=self.submit({**self.order,'Exchange':'NSE','symbol':'INFY','option_type':None,'trade_symbol':'INFY'})
        self.master.assert_not_called()
        self.assertEqual(place.call_args.args[4],'INFY')
