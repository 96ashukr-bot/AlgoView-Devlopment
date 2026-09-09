from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch
import inspect

from django.test import TestCase, SimpleTestCase
from django.utils import timezone
from main.models import BrokerOrderIntent, Role, Tradeorderhistory, User
from main.services.daily_broker_sessions import IST
from main.services.exit_intents import ACTIVE_LIFECYCLES
from main.services.webhook_exit_completion import record_direct_webhook_exit_result, mark_stale_direct_webhook_exits


class AngelLoginExpiryTests(SimpleTestCase):
    def test_login_expiry_is_today_2355_before_and_after_nine_am(self):
        from main.angelone_views import _calculate_session_expiry
        for hour, minute in [(0,1),(8,0),(9,0),(12,30),(23,54),(23,55)]:
            now=datetime(2026,9,9,hour,minute,tzinfo=IST)
            with self.subTest(time=now), patch('django.utils.timezone.now',return_value=now):
                self.assertEqual(_calculate_session_expiry(),datetime(2026,9,9,23,55,tzinfo=IST))


class WebhookExitCompletionTests(TestCase):
    def setUp(self):
        role=Role.objects.create(name='exit-completion-test')
        self.user=User.objects.create_user(email='exit-completion@example.test',firstName='Test',lastName='Client',phoneNumber='9000000992',password='test',role=role)
        self.trade=Tradeorderhistory.objects.create(client=self.user,broker='Angel One',transaction_type='BUY',order_status='complete',trade_order_status='OPEN',EntryQty=65)
        self.intent=BrokerOrderIntent.objects.create(client=self.user,broker='angel one',idempotency_key='completion-test',kind='exit',account_partition='angelone:test',source_type='webhook_exit_direct',source_id=str(self.trade.pk),exit_trade_history=self.trade,lifecycle_state='submitting',status='published',remaining_quantity=65,requested_quantity=65,heartbeat_at=timezone.now())

    def record(self,response,**kwargs):
        result=record_direct_webhook_exit_result(self.intent.pk,client_id=kwargs.get('client_id',self.user.pk),side=kwargs.get('side','SELL'),response=response,history_id='test-history')
        self.intent.refresh_from_db()
        return result

    def test_pre_submission_token_failure_releases_active_state(self):
        self.record({'data':{'status':'Failed','error_code':'DAILY_BROKER_TOKEN_REQUIRED','message':'Generate today token'}})
        self.assertEqual(self.intent.status,'rejected')
        self.assertNotIn(self.intent.lifecycle_state,ACTIVE_LIFECYCLES)
        self.assertEqual(self.intent.last_error,'Generate today token')

    def test_timeout_remains_duplicate_protected(self):
        self.record({'data':{'status':'Failed','message':'Order placement timed out'}})
        self.assertEqual(self.intent.lifecycle_state,'submission_uncertain')
        self.assertIn(self.intent.lifecycle_state,ACTIVE_LIFECYCLES)
        self.assertEqual(self.intent.remaining_quantity,65)

    def test_broker_acknowledgement_is_saved_without_inventing_fill(self):
        self.record({'data':{'status':'open','order_id':'BROKER-1'}})
        self.assertEqual(self.intent.lifecycle_state,'broker_accepted')
        self.assertEqual(self.intent.broker_order_id,'BROKER-1')
        self.assertEqual(self.intent.remaining_quantity,65)
        self.assertIsNone(self.intent.filled_at)

    def test_success_without_order_id_remains_uncertain(self):
        self.record({'data':{'status':'success'}})
        self.assertEqual(self.intent.lifecycle_state,'submission_uncertain')

    def test_confirmed_closed_trade_is_reconciled(self):
        self.trade.trade_order_status='CLOSED';self.trade.save(update_fields=['trade_order_status'])
        self.record({'data':{'status':'complete','order_id':'BROKER-1'}})
        self.assertEqual(self.intent.lifecycle_state,'reconciled')
        self.assertEqual(self.intent.remaining_quantity,0)

    def test_entry_leg_and_foreign_client_cannot_overwrite_exit(self):
        self.assertFalse(self.record({'status':'Failed'},side='BUY'))
        self.assertFalse(self.record({'status':'Failed'},client_id=self.user.pk+999))
        self.assertEqual(self.intent.lifecycle_state,'submitting')

    def test_recorded_fill_cannot_be_downgraded(self):
        self.intent.lifecycle_state='filled';self.intent.save(update_fields=['lifecycle_state'])
        self.assertFalse(self.record({'status':'Failed'}))
        self.assertEqual(self.intent.lifecycle_state,'filled')

    def test_stale_worker_is_marked_uncertain_and_not_replayed(self):
        now=timezone.now()
        self.assertEqual(mark_stale_direct_webhook_exits(now=now),0)
        self.assertEqual(mark_stale_direct_webhook_exits(now=now+timedelta(minutes=7)),1)
        self.assertEqual(mark_stale_direct_webhook_exits(now=now+timedelta(minutes=8)),0)
        self.intent.refresh_from_db()
        self.assertEqual(self.intent.lifecycle_state,'submission_uncertain')
        self.assertIn(self.intent.lifecycle_state,ACTIVE_LIFECYCLES)

    def test_joining_existing_exit_does_not_reset_state_or_heartbeat(self):
        from main.views import _bind_webhook_close_to_open_buy
        self.intent.lifecycle_state='broker_accepted';self.intent.save(update_fields=['lifecycle_state'])
        original_heartbeat=self.intent.heartbeat_at
        with patch('main.brokers.position_guard.find_matching_open_buy_position',return_value=self.trade),patch('main.brokers.position_guard.history_strike',return_value=23500),patch('main.services.exit_intents.reserve_exit_intent',return_value=(self.intent,False)):
            result=_bind_webhook_close_to_open_buy(user=self.user,broker='Angel One',group_service='',symbol='NIFTY',strike=23500,option_type='PE',expiry='2026-09-15',order_params={})
        self.intent.refresh_from_db()
        self.assertEqual(self.intent.lifecycle_state,'broker_accepted')
        self.assertEqual(self.intent.heartbeat_at,original_heartbeat)
        self.assertTrue(result['exit_intent_joined_existing'])

    def test_direct_webhook_wrapper_records_engine_validation_failure(self):
        from main.views import place_order_broker
        kwargs={name:None for name in inspect.signature(place_order_broker).parameters}
        kwargs.update(user=self.user,trade=SimpleNamespace(broker='Angel One'),transaction_type='SELL',symbol='NIFTY',order_params={'broker_order_intent_id':self.intent.pk},history_id='test-history')
        response={'data':{'status':'Failed','error_code':'INVALID_SESSION','message':'Reconnect broker'}}
        engine=Mock();engine.execute_order.return_value=response
        with patch('main.views.ExecutionRequest'),patch('main.views.get_execution_engine',return_value=engine),patch('main.views.save_trade_order_history'):
            self.assertEqual(place_order_broker(**kwargs),response)
        self.intent.refresh_from_db()
        self.assertEqual(self.intent.lifecycle_state,'manual_attention')
        self.assertEqual(self.intent.last_error,'Reconnect broker')

    def test_late_failure_cannot_downgrade_broker_accepted_order(self):
        self.intent.lifecycle_state='broker_accepted';self.intent.save(update_fields=['lifecycle_state'])
        self.assertFalse(self.record({'data':{'status':'Failed','error_code':'INVALID_SESSION'}}))
        self.assertEqual(self.intent.lifecycle_state,'broker_accepted')


class AngelFreshCallbackTests(SimpleTestCase):
    def test_fresh_token_verifies_before_replacing_expired_saved_session(self):
        from main.angelone.services.auth_service import AuthService
        manager=Mock()
        session=Mock(access_token='fresh-test-token',refresh_token='test-refresh',feed_token='test-feed')
        session.session_expiry=datetime(2026,9,9,23,55,tzinfo=IST)
        session.to_dict.return_value={}
        manager.create_session_from_tokens.return_value=session
        manager.validate_session.return_value={'status':'success','session':session}
        details=Mock(isTokenExpired=True)
        details.access_token_expiry=session.session_expiry
        details.execution_node=None
        with patch('main.angelone.services.auth_service.SessionManager.get_instance',return_value=manager):
            result=AuthService().register_existing_tokens(client_id='test',api_key='test',access_token='fresh-test-token',broker_details=details,verify_remote=True)
        self.assertEqual(result['status'],'success')
        self.assertIsNone(manager.validate_session.call_args.kwargs['broker_details'])
        self.assertTrue(manager.validate_session.call_args.kwargs['verify_remote'])
        self.assertTrue(details.set_session_tokens.call_args.kwargs['mark_token_created'])

    def test_rejected_fresh_token_cannot_replace_saved_credentials(self):
        from main.angelone.services.auth_service import AuthService
        manager=Mock()
        manager.validate_session.return_value={'status':'error','message':'Invalid token'}
        details=Mock(isTokenExpired=True)
        with patch('main.angelone.services.auth_service.SessionManager.get_instance',return_value=manager):
            result=AuthService().register_existing_tokens(client_id='test',api_key='test',access_token='invalid-test-token',broker_details=details,verify_remote=True)
        self.assertEqual(result['status'],'error')
        details.set_session_tokens.assert_not_called()
        details.save.assert_not_called()


class SavedTokenRejectionRecoveryTests(TestCase):
    def setUp(self):
        WebhookExitCompletionTests.setUp(self)
        self.intent.lifecycle_state = 'submission_uncertain'
        self.intent.heartbeat_at = timezone.now() - timedelta(minutes=10)
        self.intent.save(update_fields=['lifecycle_state', 'heartbeat_at'])
        self.failure = Tradeorderhistory.objects.create(
            client=self.user, transaction_type='SELL', order_status='Failed',
            order_params={'broker_order_intent_id': self.intent.pk, 'original_history_id': str(self.trade.pk)},
            response_data={'data': {'status': 'Failed', 'error_code': 'DAILY_BROKER_TOKEN_REQUIRED', 'message': 'Generate today token'}},
        )

    def recover(self):
        from main.services.webhook_exit_completion import recover_saved_token_rejection
        result = recover_saved_token_rejection(self.intent.pk)
        self.intent.refresh_from_db()
        return result

    def test_exact_saved_rejection_releases_only_ledger_and_is_idempotent(self):
        self.assertTrue(self.recover())
        self.assertEqual(self.intent.lifecycle_state, 'manual_attention')
        self.assertEqual(self.intent.status, 'rejected')
        self.assertFalse(self.recover())
        self.trade.refresh_from_db()
        self.assertEqual(self.trade.trade_order_status, 'OPEN')
        self.assertEqual(BrokerOrderIntent.objects.count(), 1)

    def test_string_intent_id_and_buy_history_id_supported(self):
        self.trade.history_id = 'original-buy'; self.trade.save(update_fields=['history_id'])
        self.failure.order_params = {'broker_order_intent_id': str(self.intent.pk), 'original_history_id': 'original-buy'}
        self.failure.save(update_fields=['order_params'])
        self.assertTrue(self.recover())

    def test_foreign_intent_or_buy_binding_cannot_release(self):
        for params in [
            {'broker_order_intent_id': self.intent.pk + 99, 'original_history_id': str(self.trade.pk)},
            {'broker_order_intent_id': self.intent.pk, 'original_history_id': 'unrelated-buy'},
            {'broker_order_intent_id': self.intent.pk, 'original_history_id': str(self.trade.pk), 'webhook_bound_open_history_id': 'unrelated-buy'},
        ]:
            self.failure.order_params = params; self.failure.save(update_fields=['order_params'])
            self.assertFalse(self.recover())

    def test_foreign_client_cannot_release(self):
        self.failure.client = User.objects.create_user(email='other-recovery@example.test', firstName='Other', lastName='Client', phoneNumber='9000000993', role=self.user.role)
        self.failure.save(update_fields=['client'])
        self.assertFalse(self.recover())

    def test_timeout_or_generic_failure_cannot_release(self):
        for code in ['', 'NETWORK_TIMEOUT']:
            self.failure.response_data = {'data': {'status': 'Failed', 'error_code': code}}
            self.failure.save(update_fields=['response_data'])
            self.assertFalse(self.recover())

    def test_accepted_or_recent_intent_cannot_release(self):
        self.intent.lifecycle_state = 'broker_accepted'; self.intent.save(update_fields=['lifecycle_state'])
        self.assertFalse(self.recover())
        self.intent.lifecycle_state = 'submission_uncertain'
        self.intent.heartbeat_at = timezone.now()
        self.intent.save(update_fields=['lifecycle_state', 'heartbeat_at'])
        self.assertFalse(self.recover())

    def test_broker_order_evidence_cannot_release(self):
        self.failure.order_id = 'ACCEPTED-1'; self.failure.save(update_fields=['order_id'])
        self.assertFalse(self.recover())
        self.failure.order_id = ''; self.failure.save(update_fields=['order_id'])
        self.intent.broker_order_id = 'ACCEPTED-1'; self.intent.save(update_fields=['broker_order_id'])
        self.assertFalse(self.recover())

    def test_newer_unknown_or_success_result_cannot_be_hidden_by_old_failure(self):
        latest = Tradeorderhistory.objects.create(
            client=self.user, transaction_type='SELL', order_params=self.failure.order_params,
            response_data={'data': {'status': 'Failed', 'message': 'Timeout'}},
        )
        self.assertFalse(self.recover())
        latest.response_data = {'data': {'status': 'success', 'order_id': 'BROKER-1'}}
        latest.save(update_fields=['response_data'])
        self.assertFalse(self.recover())
