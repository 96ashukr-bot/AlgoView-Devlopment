from types import SimpleNamespace

from django.test import TestCase
from django.utils import timezone

from main.execution_engine import ExecutionRequest, get_execution_engine
from main.models import Broker, ClientBrokerdetails, ClientTradeSetting, Role, User


class EntryAuthorizationTests(TestCase):
    def setUp(self):
        client_role, _ = Role.objects.get_or_create(name="Client")
        self.client_user = User.objects.create_user(
            email="entry-gate@example.com",
            phoneNumber="9000000771",
            firstName="Entry",
            lastName="Gate",
            password="test",
            role=client_role,
            is_active=True,
            is_enable=True,
            client_status=True,
        )
        self.trade = ClientTradeSetting.objects.create(
            client=self.client_user,
            symbol="NIFTY",
            broker="Angel One",
            quantity=65,
            is_tread_status=True,
        )

    def _request(self, transaction_type="BUY"):
        return SimpleNamespace(
            user=self.client_user,
            trade=self.trade,
            transaction_type=transaction_type,
            is_position_exit_order=False,
            is_exit_order=transaction_type == "SELL",
            broker_name="angel one",
        )

    def test_client_wide_off_blocks_queued_buy_at_dispatch_boundary(self):
        User.objects.filter(pk=self.client_user.pk).update(is_enable=False)
        result = get_execution_engine()._validate_entry_authorization(self._request())
        self.assertEqual(result["error_code"], "CLIENT_TRADING_DISABLED")

    def test_script_off_blocks_queued_buy_at_dispatch_boundary(self):
        ClientTradeSetting.objects.filter(pk=self.trade.pk).update(is_tread_status=False)
        result = get_execution_engine()._validate_entry_authorization(self._request())
        self.assertEqual(result["error_code"], "SCRIPT_TRADING_DISABLED")

    def test_exit_remains_available_when_client_trading_is_off(self):
        User.objects.filter(pk=self.client_user.pk).update(is_enable=False)
        self.assertIsNone(get_execution_engine()._validate_entry_authorization(self._request("SELL")))

    def test_old_angel_one_login_cannot_authorize_new_buy(self):
        broker = Broker.objects.create(broker_name="Angel One")
        details = ClientBrokerdetails.objects.create(
            client=self.client_user,
            broker_name=broker,
        )
        ClientBrokerdetails.objects.filter(pk=details.pk).update(
            tokenCreatedAt=timezone.now() - timezone.timedelta(days=1)
        )
        result = get_execution_engine()._validate_entry_authorization(self._request())
        self.assertEqual(result["error_code"], "ANGEL_ONE_DAILY_LOGIN_REQUIRED")
