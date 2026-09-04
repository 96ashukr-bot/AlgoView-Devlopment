from __future__ import annotations

import asyncio
import json
import logging
import os
import socket
import time
import uuid
from concurrent.futures import ThreadPoolExecutor

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import close_old_connections

from main.models import BrokerOrderIntent
from main.services.order_gateway import account_sequence_lock, acquire_rate_capacity, execute_intent
from main.services.order_streams import (
    broker_slug, claim_for_submission, record_outcome, redis_client, republish_outbox, stream_name,
)

logger = logging.getLogger("main")

FINALIZE_LUA = """
redis.call('XADD',KEYS[1],'*','intent_id',ARGV[1],'status',ARGV[2],'at',ARGV[3])
redis.call('XACK',KEYS[2],ARGV[4],ARGV[5])
return 1
"""


class Command(BaseCommand):
    help = "Run a durable per-broker Redis Stream order gateway."

    def add_arguments(self, parser):
        parser.add_argument("--broker", required=True)
        parser.add_argument("--kind", choices=("entry", "exit"), required=True)
        parser.add_argument("--concurrency", type=int, default=32)
        parser.add_argument("--db-concurrency", type=int, default=4)
        parser.add_argument("--batch-size", type=int, default=50)
        parser.add_argument("--consumer")

    def handle(self, *args, **options):
        if not settings.REDIS_URL:
            raise CommandError("REDIS_URL is required")
        self.broker = options["broker"]
        self.kind = options["kind"]
        self.stream = stream_name(broker=self.broker, kind=self.kind)
        self.group = f"gateway:{broker_slug(self.broker)}:{self.kind}"
        self.retry_zset = f"orders:retry:{broker_slug(self.broker)}:{self.kind}"
        self.wake_list = f"orders:wake:{broker_slug(self.broker)}:{self.kind}"
        self.fifo_wait_prefix = f"orders:fifo-wait:{broker_slug(self.broker)}:{self.kind}"
        self.consumer = options.get("consumer") or f"{socket.gethostname()}:{os.getpid()}:{uuid.uuid4().hex[:6]}"
        self.batch_size = max(1, min(500, options["batch_size"]))
        self.concurrency = max(1, min(512, options["concurrency"]))
        self.db_concurrency = max(1, min(32, options["db_concurrency"]))
        client = redis_client()
        try:
            client.xgroup_create(self.stream, self.group, id="0", mkstream=True)
        except Exception as exc:
            if "BUSYGROUP" not in str(exc):
                raise
        self.stdout.write(
            f"gateway broker={self.broker} kind={self.kind} stream={self.stream} "
            f"concurrency={self.concurrency} db_concurrency={self.db_concurrency}"
        )
        asyncio.run(self._run())

    async def _run(self):
        semaphore = asyncio.Semaphore(self.concurrency)
        executor = ThreadPoolExecutor(max_workers=self.concurrency, thread_name_prefix=f"gw-{broker_slug(self.broker)}")
        self.db_executor = ThreadPoolExecutor(
            max_workers=self.db_concurrency,
            thread_name_prefix=f"db-{broker_slug(self.broker)}",
        )
        outbox_executor = ThreadPoolExecutor(max_workers=1, thread_name_prefix=f"outbox-{broker_slug(self.broker)}")
        loop = asyncio.get_running_loop()
        last_sweep = 0.0
        outbox_task = None
        inflight = set()
        try:
            while True:
                finished = {task for task in inflight if task.done()}
                for task in finished:
                    try:
                        task.result()
                    except Exception:
                        logger.exception("Order gateway task failed outside message isolation")
                inflight.difference_update(finished)
                now = time.monotonic()
                if now - last_sweep >= 5 and (outbox_task is None or outbox_task.done()):
                    # Outbox recovery must never delay Stream consumption. Each
                    # gateway only scans its own broker/kind partition.
                    outbox_task = loop.run_in_executor(
                        outbox_executor, self._republish_partition_outbox,
                    )
                    last_sweep = now
                available = max(0, self.concurrency - len(inflight))
                if not available:
                    done, _pending = await asyncio.wait(inflight, return_when=asyncio.FIRST_COMPLETED)
                    continue
                messages = await loop.run_in_executor(executor, self._read_batch, min(self.batch_size, available))
                if not messages:
                    if not inflight:
                        await loop.run_in_executor(executor, self._recover_stale)
                    continue
                inflight.update(
                    asyncio.create_task(self._bounded(semaphore, executor, message_id, fields))
                    for message_id, fields in messages
                )
        finally:
            if inflight:
                await asyncio.gather(*inflight, return_exceptions=True)
            if outbox_task is not None:
                await asyncio.gather(outbox_task, return_exceptions=True)
            executor.shutdown(wait=True, cancel_futures=True)
            outbox_executor.shutdown(wait=True, cancel_futures=True)
            self.db_executor.shutdown(wait=True, cancel_futures=True)

    def _republish_partition_outbox(self):
        return self._db_call(
            republish_outbox,
            limit=max(self.batch_size * 4, 100),
            broker=self.broker,
            kind=self.kind,
        )

    def _db_call(self, function, *args, **kwargs):
        """Run ORM work only on the bounded database executor."""
        return self.db_executor.submit(
            self._execute_db_call, function, args, kwargs,
        ).result()

    @staticmethod
    def _execute_db_call(function, args, kwargs):
        # Healthy connections remain attached only to the small DB executor.
        # Broker/network workers therefore never consume PostgreSQL slots.
        close_old_connections()
        try:
            return function(*args, **kwargs)
        finally:
            close_old_connections()

    def _read_batch(self, count):
        client = redis_client()
        count = max(1, count)
        deferred = self._claim_woken(client, count)
        if len(deferred) < count:
            deferred.extend(self._claim_due_retries(client, count - len(deferred)))
        if deferred:
            return deferred
        response = client.xreadgroup(
            self.group, self.consumer, {self.stream: ">"}, count=count, block=200,
        )
        return response[0][1] if response else []

    def _claim_woken(self, client, count):
        message_ids = client.lpop(self.wake_list, max(1, count)) or []
        if isinstance(message_ids, str):
            message_ids = [message_ids]
        if not message_ids:
            return []
        return client.xclaim(
            self.stream, self.group, self.consumer, min_idle_time=0,
            message_ids=message_ids,
        )

    def _claim_due_retries(self, client, count):
        message_ids = client.zrangebyscore(
            self.retry_zset, 0, time.time(), start=0, num=max(1, count),
        )
        if not message_ids:
            return []
        client.zrem(self.retry_zset, *message_ids)
        return client.xclaim(
            self.stream, self.group, self.consumer, min_idle_time=0,
            message_ids=message_ids,
        )

    def _retry_soon(self, client, message_id, delay=0.15):
        client.zadd(self.retry_zset, {message_id: time.time() + max(0.05, delay)})

    def _fifo_wait_key(self, intent):
        return f"{self.fifo_wait_prefix}:{intent.account_partition}"

    def _defer_for_fifo(self, client, message_id, intent):
        score = intent.created_at.timestamp() if intent.created_at else time.time()
        client.zadd(self._fifo_wait_key(intent), {message_id: score})

    def _wake_next_fifo(self, client, intent):
        waiting = client.zpopmin(self._fifo_wait_key(intent), count=1)
        if waiting:
            client.rpush(self.wake_list, waiting[0][0])

    def _recover_stale(self):
        client = redis_client()
        try:
            response = client.xautoclaim(self.stream, self.group, self.consumer,
                                         min_idle_time=getattr(settings, "ORDER_STREAM_CLAIM_IDLE_MS", 120000),
                                         start_id="0-0", count=self.batch_size)
            messages = response[1] if response and len(response) > 1 else []
            # Recovered SUBMITTING intents are marked ambiguous by claim_for_submission;
            # they are deliberately not sent to the broker again.
            for message_id, fields in messages:
                self._process(message_id, fields)
        except Exception:
            logger.exception("Order stream stale-message recovery failed stream=%s", self.stream)

    async def _bounded(self, semaphore, executor, message_id, fields):
        async with semaphore:
            loop = asyncio.get_running_loop()
            try:
                await loop.run_in_executor(executor, self._process, message_id, fields)
            except Exception:
                logger.exception("Order stream message failed stream=%s message_id=%s", self.stream, message_id)

    def _process(self, message_id, fields):
        close_old_connections()
        client = redis_client()
        intent_id = int(fields["intent_id"])
        owner = f"{self.consumer}:{message_id}"
        try:
            intent = self._db_call(lambda: BrokerOrderIntent.objects.filter(pk=intent_id).first())
            if not intent:
                client.xack(self.stream, self.group, message_id)
                return
            with account_sequence_lock(client, intent, owner) as acquired:
                if not acquired:
                    self._retry_soon(client, message_id)
                    return
                if not acquire_rate_capacity(client, intent, time.time()):
                    self._retry_soon(client, message_id, delay=0.125)
                    return
                claimed = self._db_call(claim_for_submission, intent_id, self.consumer)
                if not claimed:
                    current = self._db_call(BrokerOrderIntent.objects.get, pk=intent_id)
                    if current.status in {BrokerOrderIntent.STATUS_AMBIGUOUS, BrokerOrderIntent.STATUS_RECONCILING}:
                        self._schedule_reconciliation(client, current)
                        self._finalize(client, message_id, current)
                    elif current.status in {
                        BrokerOrderIntent.STATUS_ACKNOWLEDGED, BrokerOrderIntent.STATUS_REJECTED,
                        BrokerOrderIntent.STATUS_DEAD_LETTER, BrokerOrderIntent.STATUS_CANCELLED,
                    }:
                        self._finalize(client, message_id, current)
                    elif current.status == BrokerOrderIntent.STATUS_PUBLISHED:
                        self._defer_for_fifo(client, message_id, current)
                    return
                try:
                    outcome = execute_intent(claimed)
                    normalized = outcome.get("data", outcome) if isinstance(outcome, dict) else {"response": str(outcome)}
                    raw_status = str(normalized.get("status") or "").casefold()
                    if raw_status in {"failed", "failure", "rejected", "error"}:
                        status = BrokerOrderIntent.STATUS_REJECTED
                    else:
                        status = BrokerOrderIntent.STATUS_ACKNOWLEDGED
                    current = self._db_call(BrokerOrderIntent.objects.get, pk=intent_id)
                    if current.status == BrokerOrderIntent.STATUS_CANCELLED:
                        claimed.status = BrokerOrderIntent.STATUS_CANCELLED
                        self._finalize(client, message_id, claimed)
                        return
                    self._db_call(record_outcome, intent_id, status=status, outcome=normalized)
                    if claimed.kind == BrokerOrderIntent.KIND_EXIT:
                        from main.services.exit_intents import reconcile_intent_from_trade
                        self._db_call(reconcile_intent_from_trade, intent_id)
                    claimed.status = status
                    self._finalize(client, message_id, claimed)
                except (TimeoutError, ConnectionError) as exc:
                    self._db_call(
                        record_outcome, intent_id,
                        status=BrokerOrderIntent.STATUS_AMBIGUOUS, error=str(exc),
                    )
                    claimed.status = BrokerOrderIntent.STATUS_AMBIGUOUS
                    self._schedule_reconciliation(client, claimed)
                    self._finalize(client, message_id, claimed)
                except Exception as exc:
                    # Unknown SDK/network exceptions may occur after the broker received
                    # the request. Never blind-retry; reconciliation decides the outcome.
                    self._db_call(
                        record_outcome, intent_id,
                        status=BrokerOrderIntent.STATUS_AMBIGUOUS, error=str(exc),
                    )
                    claimed.status = BrokerOrderIntent.STATUS_AMBIGUOUS
                    self._schedule_reconciliation(client, claimed)
                    self._finalize(client, message_id, claimed)
        finally:
            close_old_connections()

    def _schedule_reconciliation(self, client, intent):
        not_before = (intent.reconcile_after.timestamp() if intent.reconcile_after else time.time() + 5)
        client.zadd("orders:reconcile:delayed", {str(intent.pk): not_before})

    def _finalize(self, client, message_id, intent):
        result_stream = f"orders:results:{broker_slug(intent.broker)}"
        client.eval(FINALIZE_LUA, 2, result_stream, self.stream, str(intent.pk), intent.status,
                    time.time(), self.group, message_id)
        self._wake_next_fifo(client, intent)
