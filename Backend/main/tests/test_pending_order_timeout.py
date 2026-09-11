from dataclasses import replace
from datetime import datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import patch, Mock
from zoneinfo import ZoneInfo

from django.test import TestCase, SimpleTestCase, override_settings
from django.utils import timezone
from main.models import User, Tradeorderhistory, PendingOrderTimeout
from main.services.pending_order_brokers import PendingBrokerOrder, normalize_order, PendingOrderClient
from main.services.pending_order_timeout import decide, trade_terminal_updates, process_timeout, discover_and_dispatch, apply_terminal
from main.brokers.position_guard import remaining_open_quantity, _history_matches_open_buy

NOW=datetime(2026,9,11,14,1,0,tzinfo=ZoneInfo('Asia/Kolkata'))

def order(side='BUY', status='OPEN', filled=0, **kwargs):
    values=dict(order_id='broker-1',side=side,status=status,quantity=65,filled=filled,
                symbol='NIFTY2691523400CE',instrument_id='47293',exchange='NFO',product='MIS',
                average_price='100' if filled else '',created_at=NOW-timedelta(seconds=60),executed_at=NOW if filled else None)
    values.update(kwargs)
    return PendingBrokerOrder(**values)


class TimeoutDecisionTests(SimpleTestCase):
    def test_both_sides_never_cancel_before_sixty_seconds(self):
        for side in ['BUY','SELL']:
            for age in [0,1,59,59.999]:
                row=order(side,created_at=NOW-timedelta(seconds=age))
                self.assertEqual(decide(row,first_seen_at=NOW,pending_since=None,now=NOW)[0],'WAIT')
            self.assertEqual(decide(order(side),first_seen_at=NOW,pending_since=None,now=NOW)[0],'CANCEL')

    def test_restart_preserves_deadline(self):
        since=NOW-timedelta(seconds=61)
        action,actual=decide(order(created_at=None),first_seen_at=NOW,pending_since=since,now=NOW)
        self.assertEqual(action,'CANCEL');self.assertEqual(actual,since)

    def test_missing_broker_time_waits_full_minute(self):
        self.assertEqual(decide(order(created_at=None),first_seen_at=NOW,pending_since=None,now=NOW)[0],'WAIT')

    def test_future_time_blocks(self):
        with self.assertRaisesRegex(ValueError,'future'):
            decide(order(created_at=NOW+timedelta(seconds=1)),first_seen_at=NOW,pending_since=None,now=NOW)

    def test_filled_and_terminal_orders_are_never_cancelled(self):
        for side in ['BUY','SELL']:
            for row in [order(side,'COMPLETE',65),order(side,'CANCELLED'),order(side,'CANCELLED',20)]:
                self.assertEqual(decide(row,first_seen_at=NOW,pending_since=None,now=NOW)[0],'TERMINAL')

    def test_cancel_in_progress_is_read_only(self):
        self.assertEqual(decide(order(status='CANCEL_PENDING'),first_seen_at=NOW,pending_since=None,now=NOW)[0],'CONFIRM')

    def test_partial_fill_keeps_position_not_closed(self):
        buy=trade_terminal_updates('BUY',order(status='CANCELLED',filled=20))
        self.assertEqual((buy['trade_order_status'],buy['EntryQty'],buy['Entry_Price']),('OPEN',20,Decimal('100')))
        sell=trade_terminal_updates('SELL',order('SELL','CANCELLED',20))
        self.assertEqual((sell['trade_order_status'],sell['ExitQty']),('PARTIAL',20))

    def test_zero_fill_cancellation_has_no_price_or_profit(self):
        for side in ['BUY','SELL']:
            changes=trade_terminal_updates(side,order(side,'CANCELLED'))
            self.assertEqual(changes['trade_order_status'],'CANCELLED')
            self.assertIsNone(changes['Total'])
            self.assertIsNone(changes['Entry_Price'] if side=='BUY' else changes['Exit_Price'])

    def test_unknown_status_and_inconsistent_complete_are_blocked(self):
        for row in [order(status='UNKNOWN'),order(status='COMPLETE',filled=20)]:
            with self.assertRaises(ValueError):decide(row,first_seen_at=NOW,pending_since=None,now=NOW)

    def test_normalization_rejects_missing_fill_and_wrong_side(self):
        row={'order_id':'o1','transaction_type':'BUY','quantity':65,'status':'OPEN'}
        with self.assertRaises(ValueError):normalize_order('zerodha',row,'o1','BUY')
        row['filled_quantity']=0
        with self.assertRaises(ValueError):normalize_order('zerodha',row,'o1','SELL')
        with self.assertRaises(ValueError):normalize_order('zerodha',row,'other','BUY')

    def test_normalizes_all_eight_brokers(self):
        fixtures={
          'zerodha':{'order_id':'o1','transaction_type':'SELL','quantity':65,'filled_quantity':0,'status':'OPEN'},
          'upstox':{'order_id':'o1','transaction_type':'SELL','quantity':65,'filled_quantity':0,'status':'open'},
          'angel one':{'orderid':'o1','transactiontype':'SELL','quantity':'65','filledshares':'0','orderstatus':'open'},
          'alice blue':{'brokerOrderId':'o1','transactionType':'SELL','quantity':65,'filledQuantity':0,'orderStatus':'OPEN'},
          'dhan':{'orderId':'o1','transactionType':'SELL','quantity':65,'filledQty':0,'orderStatus':'PENDING'},
          'fyers':{'id':'o1','side':-1,'qty':65,'filledQty':0,'status':6},
          'groww':{'groww_order_id':'o1','transaction_type':'SELL','quantity':65,'filled_quantity':0,'order_status':'OPEN'},
          '5paisa':{'BrokerOrderId':'o1','BuySell':'S','Qty':65,'PendingQty':65,'OrderStatus':'Pending'},
        }
        for broker,row in fixtures.items():
            with self.subTest(broker=broker):
                normalized=normalize_order(broker,row,'o1','SELL')
                self.assertEqual(normalized.filled,0);self.assertEqual(normalized.remaining,65)

    def test_cancellation_transport_is_proxy_bound_and_never_places_orders(self):
        for broker in ['zerodha','upstox','angel one','alice blue','dhan','fyers','groww','5paisa']:
            details=SimpleNamespace(broker_name=SimpleNamespace(broker_name=broker),broker_API_KEY='test-key',execution_node=SimpleNamespace(ip_address='192.0.2.1'))
            with patch('main.services.pending_order_brokers.get_access_token',return_value='test-token'),patch('main.services.pending_order_brokers.requests.request') as request:
                request.return_value.content=b'{}';request.return_value.json.return_value={}
                client=PendingOrderClient(details,{'https':'http://assigned-proxy'})
                client.cancel(order('SELL',segment='FNO',exchange_order_id='ex-1'))
                args=request.call_args
                self.assertEqual(args.kwargs['proxies'],{'https':'http://assigned-proxy'})
                self.assertNotIn('place',args.args[1].lower())
                self.assertNotIn('create',args.args[1].lower())

    def test_disabled_monitor_is_not_scheduled_on_startup(self):
        import os
        import subprocess
        import sys
        from django.conf import settings
        code = (
            "from algoview.celery import app; from django.conf import settings; "
            "assert ('expire-pending-buy-and-sell-orders' in app.conf.beat_schedule) "
            "== settings.PENDING_ORDER_TIMEOUT_ENABLED"
        )
        for flag in ['False', 'True']:
            with self.subTest(enabled=flag):
                env = dict(os.environ, APP_ENV='test', PENDING_ORDER_TIMEOUT_ENABLED=flag,
                           DB_ENGINE='django.db.backends.sqlite3', DB_NAME=':memory:',
                           PYTHONDONTWRITEBYTECODE='1')
                result = subprocess.run([sys.executable, '-c', code], cwd=settings.BASE_DIR,
                                        env=env, capture_output=True, text=True, timeout=20)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_no_proxy_is_fail_closed(self):
        with self.assertRaisesRegex(ValueError,'proxy'):PendingOrderClient(None,None)


@override_settings(PENDING_ORDER_TIMEOUT_ENABLED=True)
class TimeoutPersistenceTests(TestCase):
    def setUp(self):
        self.user=User.objects.create_user(email='pending-timeout@example.com',firstName='Timeout',lastName='Test',phoneNumber='9000000011',password='test-only')
        self.trade=Tradeorderhistory.objects.create(client=self.user,broker='Zerodha',transaction_type='BUY',order_id='broker-1',order_status='OPEN',trade_order_status='OPEN',EntryQty=65,Entry_Price=100,Index_Symbol='NIFTY',order_params={'symbol':'NIFTY','strike':23400,'option_type':'CE','expiry':'2026-09-15'},history_id='timeout-buy-1')
        self.watch=PendingOrderTimeout.objects.create(trade=self.trade,client=self.user,broker='zerodha',broker_order_id='broker-1',side='BUY',first_seen_at=NOW-timedelta(seconds=61),next_check_at=NOW)
        self.now_patch=patch('main.services.pending_order_timeout.timezone.now',return_value=NOW);self.now_patch.start();self.addCleanup(self.now_patch.stop)
        self.detail_patch=patch('main.services.pending_order_timeout._broker_details_for_trade',return_value=SimpleNamespace(execution_node=object(),broker_name=SimpleNamespace(broker_name='Zerodha')));self.detail_patch.start();self.addCleanup(self.detail_patch.stop)
        self.policy_patch=patch('main.services.pending_order_timeout.session_policy_error',return_value=None);self.policy=self.policy_patch.start();self.addCleanup(self.policy_patch.stop)
        self.proxy_patch=patch('main.services.pending_order_timeout.build_requests_proxy_config',return_value={'https':'http://proxy'});self.proxy_patch.start();self.addCleanup(self.proxy_patch.stop)
        self.client_patch=patch('main.services.pending_order_timeout.PendingOrderClient');self.client_factory=self.client_patch.start();self.addCleanup(self.client_patch.stop)
        self.broker=self.client_factory.return_value;self.broker.broker='zerodha'

    def test_due_buy_cancel_confirmed_removes_false_position(self):
        self.broker.read.side_effect=[order(),order(status='CANCELLED')]
        result=process_timeout(self.watch.pk)
        self.trade.refresh_from_db();self.watch.refresh_from_db()
        self.assertEqual(result['status'],'terminal');self.assertEqual(self.trade.trade_order_status,'CANCELLED')
        self.assertEqual(self.trade.EntryQty,0);self.assertIsNone(self.trade.Entry_Price);self.assertIsNone(self.trade.Total)
        self.assertEqual(self.watch.cancel_attempts,1);self.assertEqual(self.watch.state,'TERMINAL')
        process_timeout(self.watch.pk);self.broker.cancel.assert_called_once()

    def test_broker_complete_before_check_no_cancel(self):
        self.broker.read.return_value=order(status='COMPLETE',filled=65)
        process_timeout(self.watch.pk);self.broker.cancel.assert_not_called()
        self.trade.refresh_from_db();self.assertEqual(self.trade.trade_order_status,'OPEN')

    def test_fill_during_cancel_is_saved_as_position(self):
        self.broker.read.side_effect=[order(),order(status='COMPLETE',filled=65)]
        process_timeout(self.watch.pk);self.trade.refresh_from_db()
        self.assertEqual(self.trade.EntryQty,65);self.assertEqual(self.trade.order_status,'complete');self.assertEqual(self.trade.trade_order_status,'OPEN')

    def test_partial_buy_cancel_keeps_filled_quantity_exitable(self):
        self.broker.read.side_effect=[order(filled=20),order(status='CANCELLED',filled=20)]
        process_timeout(self.watch.pk);self.trade.refresh_from_db()
        self.assertEqual(self.trade.EntryQty,20);self.assertEqual(self.trade.order_status,'partially_filled')
        self.assertTrue(_history_matches_open_buy(self.trade,'CE'))
        self.assertEqual(remaining_open_quantity(self.trade),20)

    def make_sell(self):
        self.trade.order_status='complete';self.trade.save(update_fields=['order_status'])
        sell=Tradeorderhistory.objects.create(client=self.user,broker='Zerodha',transaction_type='SELL',order_id='sell-1',order_status='OPEN',trade_order_status='CLOSE',EntryQty=65,ExitQty=65,Exit_Price=150,order_params={'original_history_id':self.trade.history_id},history_id='timeout-sell-1')
        watch=PendingOrderTimeout.objects.create(trade=sell,client=self.user,broker='zerodha',broker_order_id='sell-1',side='SELL',first_seen_at=NOW-timedelta(seconds=61),next_check_at=NOW)
        return sell,watch

    def test_zero_fill_sell_cancel_keeps_original_buy_open(self):
        sell,watch=self.make_sell()
        self.broker.read.side_effect=[order('SELL',order_id='sell-1'),order('SELL','CANCELLED',order_id='sell-1')]
        process_timeout(watch.pk);self.trade.refresh_from_db();sell.refresh_from_db()
        self.assertEqual(self.trade.trade_order_status,'OPEN');self.assertIsNone(self.trade.Exit_Price)
        self.assertTrue(self.trade.sltp_manual_attention);self.assertEqual(sell.ExitQty,0)
        self.assertEqual(remaining_open_quantity(self.trade),65)

    def test_partial_sell_cancel_reserves_only_remaining_position(self):
        sell,watch=self.make_sell()
        self.broker.read.side_effect=[order('SELL',filled=20,order_id='sell-1'),order('SELL','CANCELLED',20,order_id='sell-1')]
        process_timeout(watch.pk);self.trade.refresh_from_db();sell.refresh_from_db()
        self.assertEqual(sell.ExitQty,20);self.assertEqual(self.trade.trade_order_status,'OPEN')
        self.assertEqual(remaining_open_quantity(self.trade),45)
        from main.services.exit_intents import _remaining_quantity
        self.assertEqual(_remaining_quantity(self.trade,{}),45)

    def test_sell_fills_during_cancellation_closes_buy_with_actual_fill(self):
        sell,watch=self.make_sell()
        self.broker.read.side_effect=[order('SELL',order_id='sell-1'),order('SELL','COMPLETE',65,order_id='sell-1',average_price='120')]
        process_timeout(watch.pk);self.trade.refresh_from_db()
        self.assertEqual(self.trade.trade_order_status,'CLOSE');self.assertEqual(self.trade.Exit_Price,Decimal('120'))
        self.assertEqual(self.trade.Total,Decimal('1300'));self.assertEqual(self.trade.SignalExit_time,NOW)

    def test_expired_token_preserves_order_and_retries(self):
        self.policy.return_value='Generate today token'
        self.assertEqual(process_timeout(self.watch.pk)['status'],'retry')
        self.broker.cancel.assert_not_called();self.broker.read.assert_not_called()

    def test_future_deadline_waits_and_is_durable(self):
        self.broker.read.return_value=order(created_at=NOW-timedelta(seconds=30))
        process_timeout(self.watch.pk);self.watch.refresh_from_db()
        self.assertEqual(self.watch.pending_since,NOW-timedelta(seconds=30))
        self.assertEqual(self.watch.next_check_at,NOW+timedelta(seconds=30));self.broker.cancel.assert_not_called()

    def test_cancel_ack_without_confirmation_is_not_terminal(self):
        self.broker.read.return_value=order()
        self.assertEqual(process_timeout(self.watch.pk)['status'],'awaiting_broker_confirmation')
        self.trade.refresh_from_db();self.assertEqual(self.trade.trade_order_status,'OPEN')

    def test_timeout_after_cancel_reads_before_retry(self):
        self.broker.cancel.side_effect=TimeoutError()
        self.broker.read.side_effect=[order(),order(status='CANCELLED')]
        self.assertEqual(process_timeout(self.watch.pk)['status'],'terminal')
        self.broker.cancel.assert_called_once()

    def test_lease_blocks_overlapping_workers(self):
        self.watch.lease_until=NOW+timedelta(seconds=30);self.watch.save()
        self.assertEqual(process_timeout(self.watch.pk)['status'],'busy_or_terminal')
        self.broker.read.assert_not_called()

    def test_cap_cancellation_attempts_without_false_closure(self):
        self.watch.cancel_attempts=3;self.watch.save();self.broker.read.return_value=order()
        self.assertEqual(process_timeout(self.watch.pk)['status'],'attention')
        self.broker.cancel.assert_not_called()

    def test_disabled_feature_never_calls_broker_or_dispatches(self):
        with override_settings(PENDING_ORDER_TIMEOUT_ENABLED=False),patch('main.tasks.expire_pending_order_task.apply_async') as dispatch:
            self.assertEqual(process_timeout(self.watch.pk)['status'],'disabled')
            self.assertEqual(discover_and_dispatch()['queued'],0)
            dispatch.assert_not_called();self.broker.read.assert_not_called()

    def test_discovery_finds_both_sides_not_untracked_broker_orders(self):
        sell,watch=self.make_sell()
        self.watch.delete();watch.delete()
        self.trade.order_status='OPEN';self.trade.save()
        with patch('main.tasks.expire_pending_order_task.apply_async') as dispatch:
            self.assertEqual(discover_and_dispatch()['queued'],2)
            self.assertEqual(set(PendingOrderTimeout.objects.values_list('side',flat=True)),{'BUY','SELL'})
            self.assertEqual(discover_and_dispatch()['queued'],0)
            self.assertEqual(dispatch.call_count,2)

    def test_duplicate_history_does_not_starve_new_orders(self):
        Tradeorderhistory.objects.create(client=self.user,broker='Zerodha',transaction_type='BUY',order_id='broker-1',order_status='OPEN')
        fresh=Tradeorderhistory.objects.create(client=self.user,broker='Zerodha',transaction_type='SELL',order_id='fresh-sell',order_status='OPEN')
        with patch('main.tasks.expire_pending_order_task.apply_async'):
            discover_and_dispatch(limit=1)
        self.assertTrue(PendingOrderTimeout.objects.filter(trade=fresh).exists())

    def test_replaced_order_id_gets_its_own_deadline(self):
        self.trade.order_id='replacement-id';self.trade.save(update_fields=['order_id'])
        with patch('main.tasks.expire_pending_order_task.apply_async'):
            discover_and_dispatch()
        self.assertTrue(PendingOrderTimeout.objects.filter(broker_order_id='replacement-id',trade=self.trade).exists())
        self.assertEqual(process_timeout(self.watch.pk)['status'],'retry')
        self.broker.read.assert_not_called()

    def test_changed_broker_blocks_cancellation(self):
        with patch('main.services.pending_order_timeout._broker_details_for_trade',return_value=SimpleNamespace(broker_name=SimpleNamespace(broker_name='Upstox'))):
            self.assertEqual(process_timeout(self.watch.pk)['status'],'retry')
        self.broker.read.assert_not_called()

    def test_later_fill_reconciliation_preserves_cancelled_partial_buy(self):
        self.broker.read.side_effect=[order(filled=20),order(status='CANCELLED',filled=20)]
        process_timeout(self.watch.pk);self.trade.refresh_from_db()
        from main.services.broker_fill_reconciliation import refresh_trade_fill_from_broker
        row={'orderId':'broker-1','orderStatus':'CANCELLED','filledQty':20,'quantity':65,
             'averagePrice':'100','tradingSymbol':'NIFTY2691523400CE','securityId':'47293',
             'exchange':'NFO','product':'MIS'}
        adapter=SimpleNamespace(get_orderbook=Mock(return_value=[row]))
        details=SimpleNamespace(broker_name=SimpleNamespace(broker_name='Zerodha'),execution_node=None)
        with patch('main.services.broker_fill_reconciliation.get_broker_adapter',return_value=adapter):
            refresh_trade_fill_from_broker(self.trade,details,force=True)
        self.trade.refresh_from_db()
        self.assertEqual(self.trade.order_status,'partially_filled')
        self.assertEqual(self.trade.EntryQty,20)
        self.assertEqual(remaining_open_quantity(self.trade),20)
        self.assertTrue(_history_matches_open_buy(self.trade,'CE'))
