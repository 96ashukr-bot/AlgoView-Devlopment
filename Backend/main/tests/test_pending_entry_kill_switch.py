from types import SimpleNamespace
from unittest.mock import Mock, patch
from contextlib import ExitStack
from django.test import SimpleTestCase
from main.services import pending_entry_kill_switch as service


class PendingEntryKillSwitchTests(SimpleTestCase):
    def setUp(self):
        self.trade = SimpleNamespace(id=7, pk=7, client_id=9, broker='Zerodha', transaction_type='BUY', order_status='OPEN', order_id='buy-1')
        self.details = SimpleNamespace(execution_node=object())
        self.adapter = Mock()
        stack = ExitStack(); self.addCleanup(stack.close)
        self.policy = stack.enter_context(patch.object(service, 'session_policy_error', return_value=None))
        stack.enter_context(patch.object(service, '_broker_details_for_trade', return_value=self.details))
        stack.enter_context(patch.object(service, 'build_requests_proxy_config', return_value={'https':'http://assigned-proxy'}))
        stack.enter_context(patch('main.brokers.registry.get_broker_adapter', return_value=self.adapter))
        self.acquire = stack.enter_context(patch('main.tasks.acquire_force_kill_dispatch', return_value='lock-token'))
        self.release = stack.enter_context(patch('main.tasks.release_force_kill_dispatch'))
        self.cancel = stack.enter_context(patch.object(service, '_cancel_entry'))
        self.persist = stack.enter_context(patch.object(service, '_record_terminal_unfilled', return_value={'status':'cancelled_entry'}))
        stack.enter_context(patch.object(service.time, 'sleep'))

    def record(self, status='OPEN', filled=0, **values):
        return dict(order_id='buy-1', transaction_type='BUY', status=status, filled_quantity=filled, **values)

    def test_zero_fill_confirmed_cancel_never_submits_sell(self):
        self.adapter.get_orderbook.side_effect = [[self.record()], [self.record('CANCELLED')]]
        result=service.handle_pending_entry_kill_switch(self.trade, initiated_by_id=3)
        self.assertEqual(result['status'],'cancelled_entry')
        self.cancel.assert_called_once()
        self.persist.assert_called_once()
        self.adapter.place_order.assert_not_called()
        self.release.assert_called_once_with(7,'lock-token')

    def test_upstox_envelope(self):
        self.trade.broker='Upstox'
        self.adapter.get_orderbook.side_effect=[{'status':'success','data':[self.record()]},{'status':'success','data':[self.record('cancelled')]}]
        self.assertEqual(service.handle_pending_entry_kill_switch(self.trade)['status'],'cancelled_entry')
        self.assertEqual(self.cancel.call_args.args[-1],'upstox')

    def test_expired_session_blocks_cancellation(self):
        self.policy.return_value='Generate today token'
        with self.assertRaisesRegex(ValueError,'today'): service.handle_pending_entry_kill_switch(self.trade)
        self.cancel.assert_not_called();self.adapter.get_orderbook.assert_not_called()

    def test_filled_entry_continues_existing_exit_path(self):
        self.adapter.get_orderbook.return_value=[self.record('COMPLETE',65)]
        self.assertIsNone(service.handle_pending_entry_kill_switch(self.trade))
        self.cancel.assert_not_called();self.persist.assert_not_called()

    def test_partial_entry_is_not_marked_cancelled(self):
        self.adapter.get_orderbook.return_value=[self.record('OPEN',20)]
        with self.assertRaisesRegex(ValueError,'partially filled'):service.handle_pending_entry_kill_switch(self.trade)
        self.cancel.assert_not_called();self.persist.assert_not_called()

    def test_fill_during_cancel_does_not_close_or_sell(self):
        self.adapter.get_orderbook.side_effect=[[self.record()],[self.record('COMPLETE',65)]]
        with self.assertRaisesRegex(ValueError,'filled while'):service.handle_pending_entry_kill_switch(self.trade)
        self.persist.assert_not_called();self.adapter.place_order.assert_not_called()

    def test_cancel_ack_without_terminal_confirmation_not_success(self):
        self.adapter.get_orderbook.return_value=[self.record()]
        with self.assertRaisesRegex(ValueError,'not confirmed'):service.handle_pending_entry_kill_switch(self.trade)
        self.cancel.assert_called_once();self.persist.assert_not_called()

    def test_cancel_timeout_reconciles_before_returning(self):
        self.cancel.side_effect=TimeoutError()
        self.adapter.get_orderbook.side_effect=[[self.record()],[self.record('CANCELLED')]]
        service.handle_pending_entry_kill_switch(self.trade)
        self.cancel.assert_called_once();self.persist.assert_called_once()

    def test_unknown_fill_quantity_blocks_cancellation(self):
        self.adapter.get_orderbook.return_value=[self.record(filled=None)]
        with self.assertRaisesRegex(ValueError,'quantity'):service.handle_pending_entry_kill_switch(self.trade)
        self.cancel.assert_not_called()

    def test_different_order_or_sell_does_not_cancel(self):
        for record in [dict(self.record(),order_id='other'),dict(self.record(),transaction_type='SELL')]:
            self.adapter.get_orderbook.return_value=[record]
            with self.assertRaisesRegex(ValueError,'exact BUY'):service.handle_pending_entry_kill_switch(self.trade)
        self.cancel.assert_not_called()

    def test_duplicate_dispatch_blocked(self):
        self.acquire.return_value=None
        with self.assertRaisesRegex(ValueError,'already processing'):service.handle_pending_entry_kill_switch(self.trade)
        self.cancel.assert_not_called()

    def test_terminal_zero_fill_reconciles_without_recancelling(self):
        self.adapter.get_orderbook.return_value=[self.record('CANCELLED')]
        service.handle_pending_entry_kill_switch(self.trade)
        self.cancel.assert_not_called();self.persist.assert_called_once()

    def test_other_broker_unchanged(self):
        self.trade.broker='Angel One'
        self.assertIsNone(service.handle_pending_entry_kill_switch(self.trade))
        self.adapter.get_orderbook.assert_not_called()



class PendingEntryTransportTests(SimpleTestCase):
    def test_upstox_cancel_routes_exact_order(self):
        with patch.object(service,'get_access_token',return_value='test-session'),patch.object(service.requests,'delete') as delete:
            delete.return_value.json.return_value={'status':'success'}
            proxy={'https':'http://assigned-proxy'}
            service._cancel_entry(SimpleNamespace(),proxy,{'order_id':'buy-1'},'upstox')
            self.assertEqual(delete.call_args.args[0],'https://api-hft.upstox.com/v3/order/cancel')
            self.assertEqual(delete.call_args.kwargs['params'],{'order_id':'buy-1'})
            self.assertEqual(delete.call_args.kwargs['proxies'],proxy)

    def test_zerodha_cancel_routes_exact_order(self):
        with patch.object(service,'get_access_token',return_value='test-session'),patch.object(service,'KiteConnect') as kite:
            proxy={'https':'http://assigned-proxy'}
            service._cancel_entry(SimpleNamespace(broker_API_KEY='test-api'),proxy,{'order_id':'buy-1','variety':'regular'},'zerodha')
            self.assertEqual(kite.call_args.kwargs['proxies'],proxy)
            kite.return_value.cancel_order.assert_called_once_with(variety='regular',order_id='buy-1')

    def test_terminal_writer_rejects_partial_fill(self):
        with self.assertRaisesRegex(ValueError,'executed or unconfirmed'):
            service._record_terminal_unfilled(None,{'status':'CANCELLED','filled_quantity':20},None)

    def test_zero_fill_persistence_clears_provisional_prices_and_profit(self):
        from contextlib import nullcontext
        trade=SimpleNamespace(pk=7,id=7,client_id=9,refresh_from_db=Mock())
        locked=SimpleNamespace(order_id='buy-1',transaction_type='BUY',trade_order_status='OPEN',order_params={},save=Mock())
        with patch.object(service.transaction,'atomic',return_value=nullcontext()),patch.object(service.Tradeorderhistory,'objects') as manager:
            manager.select_for_update.return_value.get.return_value=locked
            result=service._record_terminal_unfilled(trade,{'order_id':'buy-1','status':'CANCELLED','filled_quantity':0,'quantity':65,'price':98.55},3)
        self.assertEqual(result['status'],'cancelled_entry')
        self.assertEqual(locked.trade_order_status,'CANCELLED')
        self.assertIsNone(locked.Entry_Price)
        self.assertIsNone(locked.Exit_Price)
        self.assertIsNone(locked.Total)
        self.assertIsNone(locked.SignalExit_time)
        self.assertEqual(locked.order_params['pending_entry_cancellation']['filled_quantity'],0)
        locked.save.assert_called_once()
