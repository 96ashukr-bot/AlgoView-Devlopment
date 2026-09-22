from unittest.mock import Mock, patch
from django.test import SimpleTestCase
from kiteconnect import KiteConnect
from main.zerodha import _place_zerodha_order, place_zerodha_orders


class ZerodhaMarketProtectionTests(SimpleTestCase):
    def test_installed_sdk_sends_protection_through_existing_transport(self):
        proxy = {'https': 'http://test-proxy:8080'}
        kite = KiteConnect(api_key='test', proxies=proxy)
        for order_type in ('MARKET', 'SL-M'):
            with self.subTest(order_type=order_type), patch.object(kite, '_request', return_value={'order_id': 'test-order'}) as request:
                payload = dict(exchange='NFO', tradingsymbol='NIFTY2692223400PE', transaction_type='BUY',
                               quantity=130, product='MIS', order_type=order_type, price=0, trigger_price=None)
                self.assertEqual(_place_zerodha_order(kite, payload), 'test-order')
                request.assert_called_once()
                sent = request.call_args.kwargs['params']
                self.assertEqual(sent['market_protection'], -1)
                self.assertEqual(sent['quantity'], 130)
                self.assertNotIn('trigger_price', sent)
                self.assertEqual(kite.proxies, proxy)

    def test_supported_sdk_receives_protection(self):
        kite = Mock(VARIETY_REGULAR='regular')
        kite.place_order.return_value = 'id'
        self.assertEqual(_place_zerodha_order(kite, {'order_type':'MARKET'}), 'id')
        self.assertEqual(kite.place_order.call_args.kwargs['market_protection'], -1)
        kite._post.assert_not_called()

    def test_limit_order_keeps_price_without_protection(self):
        kite = Mock(VARIETY_REGULAR='regular')
        payload = {'order_type':'LIMIT','price':39.0}
        _place_zerodha_order(kite, payload)
        kite.place_order.assert_called_once_with(variety='regular', order_type='LIMIT', price=39.0)
        kite._post.assert_not_called()

    def test_submission_exception_is_not_retried(self):
        kite = KiteConnect(api_key='test')
        with patch.object(kite, '_request', side_effect=TimeoutError('lost acknowledgement')) as request:
            with self.assertRaises(TimeoutError):
                _place_zerodha_order(kite, dict(exchange='NFO',tradingsymbol='test',transaction_type='SELL',
                    quantity=130, product='MIS', order_type='MARKET'))
            request.assert_called_once()

    @patch('main.zerodha.CompanySmtpDetails.objects.first', new=lambda: None)
    @patch('main.zerodha.save_trade_order_history')
    @patch('main.zerodha.fetch_zerodha_option_ltp', return_value=39.0)
    @patch('main.zerodha._validate_zerodha_session')
    @patch('main.zerodha.KiteConnect')
    def test_market_execution_records_protection_and_preserves_proxy(self, kite_class, validate, ltp, save):
        kite = kite_class.return_value
        kite.VARIETY_REGULAR = 'regular'
        kite.place_order.return_value = 'order-1'
        kite.order_history.return_value = [{'status':'COMPLETE','average_price':39.0,'filled_quantity':130,
                                            'tradingsymbol':'NIFTY2692223400PE','transaction_type':'BUY'}]
        proxy = {'https':'http://test-proxy:8080'}
        response = place_zerodha_orders(39, 'Sparks Pro', 'token', 'key', 'NIFTY2692223400PE', 'BUY',
            'NIFTY',130,'test','MARKET','MIS',0,Mock(),2,'BUY',None,39,None,130,None,{},'NFO','FNO',
            'NIFTY',None,'OPEN','test-protection',proxy_config=proxy)
        kite_class.assert_called_once_with(api_key='key', proxies=proxy)
        kite.place_order.assert_called_once()
        self.assertEqual(kite.place_order.call_args.kwargs['market_protection'], -1)
        self.assertEqual(response['data']['status'], 'complete')
        self.assertTrue(any(isinstance(arg,dict) and arg.get('market_protection') == -1 for arg in save.call_args.args))
