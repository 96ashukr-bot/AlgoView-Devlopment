import asyncio
import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from rest_framework_simplejwt.tokens import AccessToken

from main.models import User
from main.permissions import get_accessible_clients_queryset
from main.sl_tp_watcher_service import get_sl_tp_watcher_service


logger = logging.getLogger("main")


class SLTPWatcherLiveConsumer(AsyncWebsocketConsumer):
    """Stream access-scoped cached LTP changes without another broker feed."""

    PRICE_INTERVAL_SECONDS = 0.25
    TRADE_REFRESH_SECONDS = 10

    async def connect(self):
        self.stream_task = None
        self.user = None
        await self.accept()

    async def disconnect(self, close_code):
        if self.stream_task:
            self.stream_task.cancel()

    async def receive(self, text_data=None, bytes_data=None):
        try:
            message = json.loads(text_data or "{}")
        except (TypeError, ValueError):
            await self.send(json.dumps({"type": "error", "message": "Invalid WebSocket message."}))
            return

        if message.get("type") != "authenticate" or self.user:
            return

        self.user = await self._authenticate(message.get("token"))
        if not self.user:
            await self.send(json.dumps({"type": "error", "message": "Authentication failed."}))
            await self.close(code=4401)
            return

        self.filters = {
            "client_id": message.get("client_id"),
            "history_id": str(message.get("history_id") or "").strip(),
        }
        await self.send(json.dumps({"type": "authenticated"}))
        self.stream_task = asyncio.create_task(self._stream_prices())

    @sync_to_async
    def _authenticate(self, raw_token):
        try:
            token = AccessToken(str(raw_token or ""))
            return User.objects.filter(id=token["user_id"], is_active=True).first()
        except Exception:
            return None

    @sync_to_async
    def _load_trades(self):
        service = get_sl_tp_watcher_service()
        client_ids = get_accessible_clients_queryset(self.user).values_list("id", flat=True)
        queryset = service._get_open_trades().filter(client_id__in=client_ids)
        if self.filters.get("client_id"):
            queryset = queryset.filter(client_id=self.filters["client_id"])
        if self.filters.get("history_id"):
            queryset = queryset.filter(history_id=self.filters["history_id"])
        return list(queryset)

    @sync_to_async
    def _read_ticks(self, trades):
        service = get_sl_tp_watcher_service()
        ticks = []
        for trade in trades:
            ltp, price_status, cache_age, subscription_status = service._get_cached_payload_status(trade)
            ticks.append({
                "trade_id": trade.id,
                "current_ltp": ltp,
                "cache_age_seconds": cache_age,
                "price_status": price_status,
                "subscription_status": subscription_status,
            })
        return ticks

    async def _stream_prices(self):
        trades = []
        last_trade_refresh = 0.0
        previous = {}
        try:
            while True:
                now = asyncio.get_running_loop().time()
                if now - last_trade_refresh >= self.TRADE_REFRESH_SECONDS:
                    trades = await self._load_trades()
                    last_trade_refresh = now
                    active_ids = {trade.id for trade in trades}
                    previous = {key: value for key, value in previous.items() if key in active_ids}

                changed = []
                for tick in await self._read_ticks(trades):
                    signature = (
                        tick.get("current_ltp"),
                        tick.get("price_status"),
                        tick.get("subscription_status"),
                    )
                    if previous.get(tick["trade_id"]) != signature:
                        previous[tick["trade_id"]] = signature
                        changed.append(tick)
                if changed:
                    await self.send(json.dumps({"type": "price_ticks", "ticks": changed}))
                await asyncio.sleep(self.PRICE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("SL/TP live-price WebSocket failed")
            await self.close(code=1011)
