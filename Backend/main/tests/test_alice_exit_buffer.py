import inspect
from decimal import Decimal
from types import SimpleNamespace
from unittest import TestCase, mock

from main.Alice_Blue_Api import place_alice_orders
from main.brokers.aliceblue import AliceBlueBroker


class AliceExitBufferTests(TestCase):
    def adapter_buffer(self, requested=None):
        details = SimpleNamespace(client=object(), broker_API_KEY='test',
                                  broker_API_UID='test', buffer_percentage=Decimal('2.500'))
        order = dict(symbol='NIFTY', transaction_type='SELL', quantity=130,
                     original_broker_instrument_key='42628', Exchange='NFO',
                     buffer_percentage=requested)
        with mock.patch.object(AliceBlueBroker, 'daily_session_error', return_value=None), mock.patch('main.brokers.aliceblue.prepare_close_order_from_open_position', return_value=(order, None, None)), \
             mock.patch('main.brokers.aliceblue.get_access_token', return_value='test'), \
             mock.patch('main.brokers.aliceblue.mark_open_position_closed'), \
             mock.patch('main.brokers.aliceblue.place_alice_orders', return_value={'data': {'status': 'open'}}) as place:
            AliceBlueBroker(details).place_order(order, proxy_config={'https': 'mock'})
        return place.call_args.kwargs['buffer_percentage']

    def test_exit_uses_account_buffer_when_request_has_none(self):
        self.assertEqual(self.adapter_buffer(), Decimal('2.500'))

    def test_explicit_buffer_takes_precedence(self):
        self.assertEqual(self.adapter_buffer(1.0), 1.0)

    def test_explicit_zero_is_preserved(self):
        self.assertEqual(self.adapter_buffer(0), 0)

    def submitted_price(self, buffer, explicit_price=None):
        args = {name: None for name, p in inspect.signature(place_alice_orders).parameters.items()
                if p.default is inspect.Parameter.empty}
        args.update(transaction_type='SELL', quantity=130, order_type='LIMIT',
                    price=explicit_price, product_type='MIS', Exchange='NFO',
                    symbol='NIFTY', trading_symbol_aliceblue='NIFTY',
                    session_id='test', proxy_config={'https': 'mock'},
                    instrument_id_override='42628', buffer_percentage=buffer)
        alice = mock.Mock(alice_session_id='test')
        alice.get_netwise_positions.return_value = [{'Token': '42628', 'LTP': '68.40', 'Netqty': '130'}]
        with mock.patch('main.Alice_Blue_Api.get_alice_saved_session', return_value=(alice, None)), \
             mock.patch('main.Alice_Blue_Api.cache_option_ltp'), \
             mock.patch('main.Alice_Blue_Api._alice_a3_request', return_value={'status': 'failed', 'message': 'mock only'}) as submit:
            place_alice_orders(**args)
        self.assertEqual(submit.call_count, 1)
        payload = submit.call_args.kwargs['json_payload'][0]
        self.assertEqual(payload['instrumentId'], '42628')
        self.assertEqual(payload['quantity'], 130)
        return payload['price']

    def test_configured_buffer_reaches_actual_exit_payload(self):
        self.assertEqual(self.submitted_price(Decimal('2.500')), 66.7)

    def test_omitted_buffer_keeps_legacy_default(self):
        self.assertEqual(self.submitted_price(None), 68.4)

    def test_explicit_limit_is_preserved(self):
        self.assertEqual(self.submitted_price(2.5, explicit_price=67.0), 67.0)
