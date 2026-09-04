from unittest import mock
from concurrent.futures import ThreadPoolExecutor

from django.test import TestCase, override_settings

from main.models import BrokerOrderIntent, Role, User
from main.management.commands.run_order_stream_gateway import Command as GatewayCommand
from main.services.order_gateway import execute_intent, rate_dimensions
from main.services.order_streams import (
    claim_for_submission, create_intent, create_intents_batch, partition_number,
    republish_outbox,
)


@override_settings(ORDER_STREAM_SHADOW_MODE=True)
class OrderStreamArchitectureTests(TestCase):
    def setUp(self):
        role = Role.objects.create(name="stream-test")
        self.client = User.objects.create_user(
            email="stream-client@example.test", firstName="Stream", lastName="Client",
            phoneNumber="9000000199", password="test", role=role, is_enable=True,
        )

    def _create(self, key="signal:1:client:1"):
        with self.captureOnCommitCallbacks(execute=False):
            return create_intent(
                idempotency_key=key, kind=BrokerOrderIntent.KIND_ENTRY,
                broker="Zerodha", client_id=self.client.id,
                source_type="manual_trade_result", source_id="123",
                payload={"trade_setting_id": 45, "execution_node_id": 8},
            )

    def test_intent_is_durable_and_idempotent(self):
        first, created = self._create()
        second, duplicate_created = self._create()
        self.assertTrue(created)
        self.assertFalse(duplicate_created)
        self.assertEqual(first.pk, second.pk)
        self.assertEqual(first.status, BrokerOrderIntent.STATUS_RESERVED)

    @mock.patch("main.services.order_streams.publish_intent", side_effect=ConnectionError("redis unavailable"))
    def test_redis_failure_keeps_committed_outbox_without_bubbling(self, _publish):
        with self.captureOnCommitCallbacks(execute=True):
            intent, created = create_intent(
                idempotency_key="redis-outage", kind="entry", broker="Zerodha",
                client_id=self.client.id, source_type="manual_trade_result", source_id="9",
            )
        self.assertTrue(created)
        intent.refresh_from_db()
        self.assertEqual(intent.status, BrokerOrderIntent.STATUS_RESERVED)

    @mock.patch("main.services.order_streams.connections.close_all")
    @mock.patch("main.services.order_streams.publish_intents_batch", return_value=1)
    def test_outbox_sweeper_closes_executor_thread_connections(self, publish, close_all):
        self._create("outbox-cleanup")
        self.assertEqual(republish_outbox(), 1)
        publish.assert_called_once()
        close_all.assert_called_once_with()

    @mock.patch("main.services.order_streams.connections.close_all")
    @mock.patch("main.services.order_streams.publish_intents_batch", return_value=1)
    def test_outbox_sweeper_only_publishes_its_broker_kind_partition(
        self, publish, _close_all,
    ):
        zerodha, _ = self._create("partition-zerodha")
        with self.captureOnCommitCallbacks(execute=False):
            create_intent(
                idempotency_key="partition-groww", kind=BrokerOrderIntent.KIND_ENTRY,
                broker="Groww", client_id=self.client.id,
                source_type="manual_trade_result", source_id="456",
            )
            create_intent(
                idempotency_key="partition-exit", kind=BrokerOrderIntent.KIND_EXIT,
                broker="Zerodha", client_id=self.client.id,
                source_type="kill_switch_exit", source_id="789",
            )

        self.assertEqual(
            republish_outbox(broker="Zerodha", kind=BrokerOrderIntent.KIND_ENTRY),
            1,
        )
        publish.assert_called_once_with([zerodha.pk])

    @mock.patch("main.services.order_streams._publish_batch_after_commit")
    def test_batch_reservation_is_idempotent_and_publishes_once(self, publish_batch):
        specs = [{
            "idempotency_key": f"batch-{index}",
            "kind": BrokerOrderIntent.KIND_ENTRY,
            "broker": "Zerodha",
            "client_id": self.client.id,
            "source_type": "manual_trade_result",
            "source_id": str(index),
            "payload": {"trade_setting_id": index},
        } for index in range(3)]
        with self.captureOnCommitCallbacks(execute=True):
            first = create_intents_batch(specs)
        with self.captureOnCommitCallbacks(execute=True):
            second = create_intents_batch(specs)

        self.assertEqual(set(first), set(second))
        self.assertEqual(BrokerOrderIntent.objects.filter(idempotency_key__in=first).count(), 3)
        self.assertEqual(publish_batch.call_count, 2)
        self.assertEqual(len(publish_batch.call_args_list[0].args[0]), 3)

    @mock.patch("main.services.order_streams.redis_client")
    def test_batch_publisher_never_moves_acknowledged_intent_backwards(self, redis_client):
        intent, _ = self._create("batch-terminal-race")
        pipeline = mock.Mock()
        redis_client.return_value.pipeline.return_value = pipeline
        pipeline.set.return_value = pipeline
        pipeline.xadd.return_value = pipeline
        pipeline.eval.return_value = pipeline
        results = iter([[True], ["10-1"], [1]])
        calls = 0
        def execute_with_ack():
            nonlocal calls
            calls += 1
            result = next(results)
            if calls == 2:
                BrokerOrderIntent.objects.filter(pk=intent.pk).update(
                    status=BrokerOrderIntent.STATUS_ACKNOWLEDGED,
                )
            return result
        pipeline.execute.side_effect = execute_with_ack

        from main.services.order_streams import publish_intents_batch
        self.assertEqual(publish_intents_batch([intent.pk]), 1)
        intent.refresh_from_db()
        self.assertEqual(intent.status, BrokerOrderIntent.STATUS_ACKNOWLEDGED)

    @mock.patch("main.management.commands.run_order_stream_gateway.close_old_connections")
    def test_gateway_db_call_runs_only_on_bounded_db_executor(self, close_old):
        command = GatewayCommand()
        command.db_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix="test-db")
        try:
            thread_name = command._db_call(
                lambda: __import__("threading").current_thread().name,
            )
        finally:
            command.db_executor.shutdown(wait=True)

        self.assertTrue(thread_name.startswith("test-db"))
        self.assertEqual(close_old.call_count, 2)

    def test_fifo_waiter_is_woken_immediately_after_predecessor_finalizes(self):
        command = GatewayCommand()
        command.wake_list = "orders:wake:zerodha:entry"
        command.fifo_wait_prefix = "orders:fifo-wait:zerodha:entry"
        intent, _ = self._create("fifo-wake")
        client = mock.Mock()
        client.zpopmin.return_value = [("12-3", intent.created_at.timestamp())]

        command._wake_next_fifo(client, intent)

        client.zpopmin.assert_called_once_with(command._fifo_wait_key(intent), count=1)
        client.rpush.assert_called_once_with(command.wake_list, "12-3")

    def test_woken_and_rate_limited_messages_are_claimed_without_stale_wait(self):
        command = GatewayCommand()
        command.stream = "orders:entry:zerodha"
        command.group = "gateway:zerodha:entry"
        command.consumer = "test-consumer"
        command.wake_list = "orders:wake:zerodha:entry"
        command.retry_zset = "orders:retry:zerodha:entry"
        client = mock.Mock()
        client.lpop.return_value = ["20-1"]
        client.xclaim.return_value = [("20-1", {"intent_id": "1"})]

        self.assertEqual(command._claim_woken(client, 5), [("20-1", {"intent_id": "1"})])
        client.xclaim.assert_called_once_with(
            command.stream, command.group, command.consumer,
            min_idle_time=0, message_ids=["20-1"],
        )

        client.reset_mock()
        client.zrangebyscore.return_value = ["21-1"]
        client.xclaim.return_value = [("21-1", {"intent_id": "2"})]
        self.assertEqual(command._claim_due_retries(client, 5), [("21-1", {"intent_id": "2"})])
        client.zrem.assert_called_once_with(command.retry_zset, "21-1")

    def test_credentials_are_forbidden_from_stream_payload(self):
        with self.assertRaisesMessage(ValueError, "Credential-like field"):
            self._create_with_payload({"access_token": "must-not-leak"})

    def _create_with_payload(self, payload):
        with self.captureOnCommitCallbacks(execute=False):
            return create_intent(
                idempotency_key="secret-test", kind="entry", broker="Zerodha",
                client_id=self.client.id, source_type="manual_trade_result", source_id="1", payload=payload,
            )

    def test_point_of_call_claim_and_lost_owner_becomes_ambiguous(self):
        intent, _ = self._create()
        BrokerOrderIntent.objects.filter(pk=intent.pk).update(status=BrokerOrderIntent.STATUS_PUBLISHED)
        claimed = claim_for_submission(intent.pk, "gateway-a")
        self.assertEqual(claimed.status, BrokerOrderIntent.STATUS_SUBMITTING)
        self.assertIsNone(claim_for_submission(intent.pk, "gateway-b"))
        intent.refresh_from_db()
        self.assertEqual(intent.status, BrokerOrderIntent.STATUS_AMBIGUOUS)
        self.assertIsNotNone(intent.reconcile_after)

    def test_later_order_for_same_account_waits_for_terminal_predecessor(self):
        first, _ = self._create("signal:first")
        second, _ = self._create("signal:second")
        BrokerOrderIntent.objects.filter(pk__in=[first.pk, second.pk]).update(status=BrokerOrderIntent.STATUS_PUBLISHED)
        self.assertIsNone(claim_for_submission(second.pk, "gateway-b"))
        BrokerOrderIntent.objects.filter(pk=first.pk).update(status=BrokerOrderIntent.STATUS_ACKNOWLEDGED)
        self.assertEqual(claim_for_submission(second.pk, "gateway-b").status, BrokerOrderIntent.STATUS_SUBMITTING)

    def test_shadow_executor_never_calls_live_manual_executor(self):
        intent, _ = self._create()
        with mock.patch("main.manual_trade_service._execute_manual_trade_result") as live:
            result = execute_intent(intent)
        live.assert_not_called()
        self.assertEqual(result["status"], "shadow")

    def test_partition_is_stable_and_rate_dimensions_are_scoped(self):
        intent, _ = self._create()
        self.assertEqual(partition_number(intent.account_partition, 32), partition_number(intent.account_partition, 32))
        dimensions = rate_dimensions(intent)
        self.assertIn(f"account:{intent.account_partition}", dimensions)
        self.assertIn("execution_node_id:8", dimensions)
