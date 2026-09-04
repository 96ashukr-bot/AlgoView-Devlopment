from unittest import mock

from django.core.cache import cache
from django.test import SimpleTestCase, override_settings

from main.services.entry_control import (
    ACCOUNT_LOCK_TTL_SECONDS,
    EXIT_TURN_WAIT_SECONDS,
    EntryAccountTurnDeferred,
    ExitAccountTurnDeferred,
    account_fifo_turn,
    account_key,
    exit_account_turn,
    reserve_entry,
    _redis_client,
)
from main.services.entry_readiness import get_or_build_match_ids, invalidate_entry_readiness


class EntryArchitectureTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_readiness_match_is_cached_and_generation_invalidation_rebuilds(self):
        builder = mock.Mock(return_value=[11, 12])
        first = get_or_build_match_ids(company_id=4, strategy="Momentum", symbol="NIFTY", builder=builder)
        second = get_or_build_match_ids(company_id=4, strategy="Momentum", symbol="NIFTY", builder=builder)
        self.assertEqual(first, [11, 12])
        self.assertEqual(second, [11, 12])
        self.assertEqual(builder.call_count, 1)

        invalidate_entry_readiness()
        get_or_build_match_ids(company_id=4, strategy="Momentum", symbol="NIFTY", builder=builder)
        self.assertEqual(builder.call_count, 2)

    def test_duplicate_reservation_is_atomic(self):
        self.assertTrue(reserve_entry("webhook:1:2:3"))
        self.assertFalse(reserve_entry("webhook:1:2:3"))

    @override_settings(REDIS_URL="redis://localhost:6379/9")
    @mock.patch("redis.Redis.from_url")
    def test_entry_control_constructs_configured_redis_client(self, from_url):
        sentinel = object()
        from_url.return_value = sentinel

        self.assertIs(_redis_client(), sentinel)
        from_url.assert_called_once_with(
            "redis://localhost:6379/9", decode_responses=True, socket_timeout=2,
        )

    def test_account_scope_is_broker_and_client_specific(self):
        self.assertEqual(account_key("Angel One", 42), "angelone:42")
        self.assertNotEqual(account_key("Angel One", 42), account_key("Zerodha", 42))

    @mock.patch("main.services.entry_control._redis_client")
    def test_out_of_turn_entry_defers_quickly_instead_of_waiting_fifteen_seconds(self, redis_client):
        client = redis_client.return_value
        client.exists.return_value = True
        client.lindex.return_value = '{"key":"an-earlier-order"}'

        with self.assertRaises(EntryAccountTurnDeferred):
            with account_fifo_turn(
                broker="Angel One",
                client_id=42,
                order_key="later-order",
                timeout=0.001,
            ):
                self.fail("An out-of-turn order must not execute.")

    @mock.patch("main.services.entry_control._redis_client")
    def test_demo_broker_exit_does_not_enter_real_account_fifo(self, redis_client):
        with exit_account_turn(broker="Demo Broker", client_id=42, order_key="demo-exit"):
            pass

        redis_client.assert_not_called()

    @mock.patch("main.services.entry_control._redis_client")
    def test_out_of_turn_exit_is_deferred_instead_of_permanently_failed(self, redis_client):
        client = redis_client.return_value
        client.exists.return_value = True
        client.lindex.return_value = '{"key":"an-earlier-exit"}'

        with self.assertRaises(ExitAccountTurnDeferred):
            with exit_account_turn(
                broker="Angel One",
                client_id=42,
                order_key="later-exit",
                timeout=0.001,
            ):
                self.fail("An out-of-turn exit must be retried, not executed.")

    def test_priority_exit_default_wait_is_non_blocking(self):
        self.assertLessEqual(EXIT_TURN_WAIT_SECONDS, 0.25)

    def test_account_lock_outlives_maximum_broker_task(self):
        self.assertGreater(ACCOUNT_LOCK_TTL_SECONDS, 300)

    @mock.patch("main.services.entry_control._durable_account_turn")
    @mock.patch("main.services.entry_control._redis_client", return_value=None)
    def test_exit_uses_durable_fallback_when_redis_is_unavailable(self, _redis, durable):
        durable.return_value = mock.MagicMock(__enter__=mock.Mock(), __exit__=mock.Mock(return_value=False))
        with exit_account_turn(broker="Angel One", client_id=42, order_key="exit-1"):
            pass
        durable.assert_called_once()
