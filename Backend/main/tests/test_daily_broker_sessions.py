from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.test import SimpleTestCase
from main.services.daily_broker_sessions import IST, capped_expiry, daily_cutoff, session_policy_error


class DailyBrokerSessionTests(SimpleTestCase):
    def setUp(self):
        self.now = datetime(2026, 9, 9, 9, 30, tzinfo=IST)
        self.details = SimpleNamespace(access_token='test', tokenCreatedAt=self.now - timedelta(minutes=30), access_token_expiry=None, isTokenExpired=False)

    def test_today_created_account_without_token_is_blocked(self):
        self.details.access_token = None
        self.assertIn("missing", session_policy_error(self.details, now=self.now))

    def test_todays_token_is_allowed(self):
        self.assertIsNone(session_policy_error(self.details, now=self.now))

    def test_yesterdays_token_is_blocked_despite_future_broker_expiry(self):
        self.details.tokenCreatedAt -= timedelta(days=1)
        self.details.access_token_expiry = self.now + timedelta(days=7)
        self.assertIn("Today's", session_policy_error(self.details, now=self.now))

    def test_missing_and_future_issuance_are_blocked(self):
        for issued in (None, self.now + timedelta(seconds=1)):
            self.details.tokenCreatedAt = issued
            self.assertIsNotNone(session_policy_error(self.details, now=self.now))

    def test_cutoff_is_inclusive_and_midnight_requires_new_token(self):
        for hour, minute, second, allowed in [(23,54,59,True),(23,55,0,False),(23,59,59,False)]:
            at=self.now.replace(hour=hour,minute=minute,second=second)
            self.assertEqual(session_policy_error(self.details, now=at) is None,allowed)
        self.assertIsNotNone(session_policy_error(self.details, now=self.now + timedelta(days=1)))

    def test_utc_date_does_not_override_ist_login_day(self):
        from datetime import timezone
        self.details.tokenCreatedAt = self.now.replace(hour=0,minute=1).astimezone(timezone.utc)
        self.assertIsNone(session_policy_error(self.details,now=self.now))

    def test_explicit_broker_expiry_and_expired_flag_are_respected(self):
        self.details.access_token_expiry = self.now
        self.assertIsNotNone(session_policy_error(self.details,now=self.now))
        self.details.access_token_expiry = None
        self.details.isTokenExpired = True
        self.assertIsNotNone(session_policy_error(self.details,now=self.now))

    def test_expiry_never_extends_broker_or_daily_deadline(self):
        self.assertEqual(capped_expiry(self.now),self.now.replace(hour=23,minute=55))
        earlier=self.now+timedelta(hours=1)
        self.assertEqual(capped_expiry(self.now, earlier), earlier)
        self.assertEqual(capped_expiry(self.now,self.now+timedelta(days=1)),daily_cutoff(self.now))

    def test_model_caps_new_token_and_refresh_cannot_change_login_day(self):
        from main.models import ClientBrokerdetails
        details=ClientBrokerdetails(tokenCreatedAt=self.now-timedelta(days=1))
        with patch.object(details,'_set_secret'), patch.object(details,'is_angel_one_broker',return_value=False), patch('django.utils.timezone.now',return_value=self.now):
            details.set_session_tokens('test',expiry=self.now+timedelta(days=1))
            self.assertTrue(details.isTokenExpired)
            details.set_session_tokens('test',expiry=self.now+timedelta(days=1),mark_token_created=True)
            self.assertFalse(details.isTokenExpired)
            self.assertEqual(details.tokenCreatedAt,self.now)
            self.assertEqual(details.access_token_expiry,daily_cutoff(self.now))

    def test_token_created_after_cutoff_is_immediately_expired(self):
        from main.models import ClientBrokerdetails
        details=ClientBrokerdetails()
        with patch.object(details,'_set_secret'), patch.object(details,'is_angel_one_broker',return_value=False), patch('django.utils.timezone.now',return_value=daily_cutoff(self.now)):
            details.set_session_tokens('test',mark_token_created=True)
            self.assertTrue(details.isTokenExpired)

    def test_every_live_adapter_blocks_before_any_broker_request(self):
        from importlib import import_module
        modules={'aliceblue':'AliceBlueBroker','angelone':'AngelOneBroker','dhan':'DhanBroker','fivepaisa':'FivePaisaBroker','fyers':'FyersBroker','groww':'GrowwBroker','upstox':'UpstoxBroker','zerodha':'ZerodhaBroker'}
        self.details.tokenCreatedAt -= timedelta(days=1)
        self.details.refresh_from_db=Mock()
        with patch('django.utils.timezone.now',return_value=self.now):
            for module,cls in modules.items():
                with self.subTest(broker=module):
                    adapter=getattr(import_module('main.brokers.'+module),cls)(self.details)
                    result=adapter.place_order({'transaction_type':'BUY'})
                    self.assertEqual(result['data']['error_code'],'DAILY_BROKER_TOKEN_REQUIRED')
        self.assertEqual(self.details.refresh_from_db.call_count,8)

    def test_queued_order_is_rechecked_at_dispatch(self):
        from main.execution_engine import ExecutionEngine
        engine=object.__new__(ExecutionEngine)
        engine._get_client_broker=Mock(return_value=self.details)
        self.details.tokenCreatedAt -= timedelta(days=1)
        with patch('django.utils.timezone.now',return_value=self.now):
            result=engine._dispatch(SimpleNamespace(broker_name='alice blue'),{})
        self.assertEqual(result['data']['error_code'],'DAILY_BROKER_TOKEN_REQUIRED')

    def test_cached_readiness_cannot_bypass_daily_policy(self):
        from main.services.broker_session_readiness import get_cached_readiness
        self.details.broker_name=SimpleNamespace(broker_name='Alice Blue')
        self.details.tokenCreatedAt -= timedelta(days=1)
        with patch('django.utils.timezone.now',return_value=self.now),patch('main.services.broker_session_readiness.cache.get',return_value={'status':'READY_LOCAL'}),patch('main.models.ClientBrokerdetails.objects') as objects:
            objects.select_related.return_value.filter.return_value.first.return_value=self.details
            self.assertIsNone(get_cached_readiness(1))

    def test_angel_cached_session_and_refresh_stop_at_cutoff(self):
        from main.angelone.managers.session_manager import ClientSession, SessionStatus
        session=ClientSession(client_id='test',api_key='test',session_key='test',access_token='test',refresh_token='test',login_time=self.now,status=SessionStatus.ACTIVE,session_expiry=self.now+timedelta(days=1))
        with patch('django.utils.timezone.now',return_value=daily_cutoff(self.now)):
            self.assertFalse(session.is_valid())
            self.assertFalse(session.can_refresh())


from django.test import TestCase


class DailyTokenCleanupTests(TestCase):
    def test_cleanup_expires_old_tokens_preserves_today_and_is_idempotent(self):
        from main.models import Broker, ClientBrokerdetails
        from main.services.daily_broker_sessions import expire_due_client_tokens
        now=datetime(2026,9,9,12,tzinfo=IST)
        broker=Broker.objects.create(broker_name='Alice Blue')
        old=ClientBrokerdetails.objects.create(broker_name=broker,isTokenExpired=False)
        fresh=ClientBrokerdetails.objects.create(broker_name=broker,isTokenExpired=False)
        ClientBrokerdetails.objects.filter(pk=old.pk).update(tokenCreatedAt=now-timedelta(days=1))
        ClientBrokerdetails.objects.filter(pk=fresh.pk).update(tokenCreatedAt=now-timedelta(hours=1))
        self.assertEqual(expire_due_client_tokens(now),1)
        old.refresh_from_db();fresh.refresh_from_db()
        self.assertTrue(old.isTokenExpired)
        self.assertFalse(fresh.isTokenExpired)
        self.assertEqual(expire_due_client_tokens(now),0)
        self.assertEqual(expire_due_client_tokens(daily_cutoff(now)),1)
        fresh.refresh_from_db()
        self.assertTrue(fresh.isTokenExpired)

    def test_delayed_cleanup_does_not_expire_next_days_new_session(self):
        from main.models import Broker, ClientBrokerdetails
        from main.services.daily_broker_sessions import expire_due_client_tokens
        now=datetime(2026,9,10,0,5,tzinfo=IST)
        broker=Broker.objects.create(broker_name='Angel One')
        fresh=ClientBrokerdetails.objects.create(broker_name=broker,isTokenExpired=False)
        ClientBrokerdetails.objects.filter(pk=fresh.pk).update(tokenCreatedAt=now-timedelta(minutes=1))
        self.assertEqual(expire_due_client_tokens(now),0)
        fresh.refresh_from_db()
        self.assertFalse(fresh.isTokenExpired)
