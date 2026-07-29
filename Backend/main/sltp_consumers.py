import asyncio
import json
import logging

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer
from django.db.models import Q
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework_simplejwt.tokens import AccessToken

from main.models import User
from main.permissions import get_accessible_clients_queryset
from main.sl_tp_watcher_service import get_sl_tp_watcher_service


logger = logging.getLogger("main")


class SLTPWatcherLiveConsumer(AsyncWebsocketConsumer):
    """Stream access-scoped cached LTP changes without another broker feed."""

    PRICE_INTERVAL_SECONDS = 1.0
    TRADE_REFRESH_SECONDS = 30

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
            "from_date": str(message.get("from_date") or "").strip(),
            "to_date": str(message.get("to_date") or "").strip(),
            "broker": str(message.get("broker") or "").strip(),
            "index_symbol": str(message.get("index_symbol") or "").strip(),
            "group_service": str(message.get("group_service") or "").strip(),
            "search": str(message.get("search") or "").strip(),
            "trade_ids": (
                {
                    int(trade_id)
                    for trade_id in (message.get("trade_ids") or [])
                    if str(trade_id).isdigit()
                }
                if "trade_ids" in message
                else None
            ),
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
        trade_ids = self.filters.get("trade_ids")
        if trade_ids is not None:
            queryset = queryset.filter(id__in=trade_ids) if trade_ids else queryset.none()
        client_id = self.filters.get("client_id")
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        history_id = self.filters.get("history_id")
        if history_id:
            queryset = queryset.filter(history_id=history_id)
        from_date = parse_date(self.filters.get("from_date"))
        to_date = parse_date(self.filters.get("to_date"))
        if from_date:
            queryset = queryset.filter(date__gte=from_date)
        if to_date:
            queryset = queryset.filter(date__lte=to_date)
        if not from_date and not to_date:
            queryset = queryset.filter(date=timezone.localdate())
        broker = self.filters.get("broker")
        if broker and broker.lower() != "all":
            queryset = queryset.filter(broker__iexact=broker)
        group_service = self.filters.get("group_service")
        if group_service and group_service.lower() != "all":
            queryset = queryset.filter(GroupService__iexact=group_service)
        index_symbol = self.filters.get("index_symbol")
        if index_symbol and index_symbol.lower() != "all":
            queryset = queryset.filter(
                Q(Index_Symbol__icontains=index_symbol)
                | Q(trading_symbol__icontains=index_symbol)
            )
        search = self.filters.get("search")
        if search:
            queryset = queryset.filter(
                Q(client__fullName__icontains=search)
                | Q(client__email__icontains=search)
                | Q(broker__icontains=search)
                | Q(Index_Symbol__icontains=search)
                | Q(trading_symbol__icontains=search)
                | Q(GroupService__icontains=search)
                | Q(order_id__icontains=search)
            )
        return list(queryset)

    @sync_to_async
    def _read_ticks(self, trades):
        service = get_sl_tp_watcher_service()
        ticks = []
        overall_running_pnl = 0.0
        for trade in trades:
            ltp, price_status, cache_age, subscription_status = service._get_cached_payload_status(trade)
            profit_ltp = ltp
            if price_status is not None or profit_ltp is None:
                profit_ltp = trade.LivePrice
            if trade.Entry_Price is not None and trade.EntryQty is not None and profit_ltp is not None:
                entry_price = float(trade.Entry_Price)
                quantity = float(trade.EntryQty)
                if str(trade.Entry_type or "").strip().upper() in {"SELL", "SHORT"}:
                    overall_running_pnl += (entry_price - float(profit_ltp)) * quantity
                else:
                    overall_running_pnl += (float(profit_ltp) - entry_price) * quantity
            ticks.append({
                "trade_id": trade.id,
                "current_ltp": ltp,
                "cache_age_seconds": cache_age,
                "price_status": price_status,
                "subscription_status": subscription_status,
            })
        return ticks, round(overall_running_pnl, 2)

    async def _stream_prices(self):
        trades = []
        last_trade_refresh = 0.0
        previous = {}
        previous_total = None
        try:
            while True:
                now = asyncio.get_running_loop().time()
                if now - last_trade_refresh >= self.TRADE_REFRESH_SECONDS:
                    trades = await self._load_trades()
                    last_trade_refresh = now
                    active_ids = {trade.id for trade in trades}
                    previous = {key: value for key, value in previous.items() if key in active_ids}

                ticks, overall_running_pnl = await self._read_ticks(trades)
                changed = []
                for tick in ticks:
                    signature = (
                        tick.get("current_ltp"),
                        tick.get("price_status"),
                        tick.get("subscription_status"),
                    )
                    if previous.get(tick["trade_id"]) != signature:
                        previous[tick["trade_id"]] = signature
                        changed.append(tick)
                if changed or overall_running_pnl != previous_total:
                    previous_total = overall_running_pnl
                    await self.send(json.dumps({
                        "type": "price_ticks",
                        "ticks": changed,
                        "overall_running_pnl": overall_running_pnl,
                    }))
                await asyncio.sleep(self.PRICE_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("SL/TP live-price WebSocket failed")
            await self.close(code=1011)
