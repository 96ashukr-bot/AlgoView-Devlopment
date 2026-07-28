from __future__ import annotations

import asyncio
import json
import logging
import re
import ssl
import time
from contextlib import nullcontext
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import requests
import websockets
from asgiref.sync import sync_to_async
from django.conf import settings
from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone
from google.protobuf.json_format import MessageToDict

from main import MarketDataFeed_pb2 as pb
from main.broker_instrument_cache import load_upstox_instruments
from main.brokers.utils import get_access_token
from main.models import ClientBrokerdetails, MarketDataCredential, Tradeorderhistory
from main.services.egress_guard import allow_direct_market_data_egress
from main.services.live_price_cache import build_live_price_payload, cache_live_price, get_live_price, normalize_symbol_key
from main.services.option_ltp_fallback import cache_option_ltp
from main.services.proxy_utils import build_requests_proxy_config


logger = logging.getLogger("main.market_data")

OPEN_ORDER_STATUSES = {
    "complete",
    "completed",
    "executed",
    "filled",
    "open",
    "pending",
    "put order req received",
    "success",
    "traded",
    "transit",
}

SUPPORTED_INDEX_UNDERLYINGS = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"}
UPSTOX_MARKET_QUOTE_LTP_URL = "https://api.upstox.com/v2/market-quote/ltp"
ZERODHA_WEEKLY_MONTH_CODES = {
    "1": 1, "2": 2, "3": 3, "4": 4, "5": 5, "6": 6,
    "7": 7, "8": 8, "9": 9, "O": 10, "N": 11, "D": 12,
}


@dataclass(frozen=True)
class UpstoxInstrument:
    instrument_key: str
    trading_symbol: str
    exchange: str
    underlying: str
    expiry_date: Optional[datetime]
    strike: Optional[float]
    option_type: str

    @property
    def aliases(self) -> tuple[str, ...]:
        items = [self.trading_symbol]
        if self.underlying and self.expiry_date and self.strike and self.option_type:
            items.append(
                f"{self.underlying}{self.expiry_date.strftime('%d%b%y').upper()}{self.strike:g}{self.option_type}"
            )
            items.append(
                f"{self.underlying}{self.expiry_date.strftime('%y%b')}{self.strike:g}{self.option_type}".upper()
            )
        return tuple(dict.fromkeys(item for item in items if item))


def _to_float(value: Any) -> Optional[float]:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _expiry_from_upstox(value: Any) -> Optional[datetime]:
    if value in (None, "", "None"):
        return None
    try:
        numeric = float(value)
    except (TypeError, ValueError):
        numeric = None
    if numeric:
        if numeric > 10_000_000_000:
            numeric = numeric / 1000.0
        return datetime.fromtimestamp(numeric, tz=timezone.get_current_timezone()).replace(
            hour=0, minute=0, second=0, microsecond=0
        )
    text = str(value).strip()
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d%b%Y", "%d%b%y"):
        try:
            parsed = datetime.strptime(text, fmt)
            return timezone.make_aware(parsed) if timezone.is_naive(parsed) else parsed
        except ValueError:
            continue
    return None


def _row_to_instrument(row: dict[str, Any]) -> Optional[UpstoxInstrument]:
    instrument_key = str(row.get("instrument_key") or "").strip()
    trading_symbol = str(row.get("trading_symbol") or "").strip()
    option_type = str(row.get("instrument_type") or row.get("option_type") or "").strip().upper()
    if not instrument_key or not trading_symbol or option_type not in {"CE", "PE"}:
        return None
    underlying = normalize_symbol_key(row.get("underlying_symbol") or row.get("asset_symbol") or row.get("name"))
    if underlying not in SUPPORTED_INDEX_UNDERLYINGS:
        return None
    strike = _to_float(row.get("strike_price") or row.get("strike"))
    expiry = _expiry_from_upstox(row.get("expiry"))
    if strike is None or not expiry:
        return None
    return UpstoxInstrument(
        instrument_key=instrument_key,
        trading_symbol=trading_symbol,
        exchange=str(row.get("exchange") or "").strip().upper(),
        underlying=underlying,
        expiry_date=expiry,
        strike=strike,
        option_type=option_type,
    )


class UpstoxInstrumentResolver:
    def __init__(self):
        self._by_symbol: dict[str, UpstoxInstrument] = {}
        self._by_contract: dict[tuple[str, str, float, str], UpstoxInstrument] = {}
        self._loaded = False

    def _load(self) -> None:
        if self._loaded:
            return
        for exchange in ("NSE", "BSE"):
            try:
                rows = load_upstox_instruments(exchange)
            except Exception as exc:
                logger.warning("Could not load Upstox %s instruments: %s", exchange, exc)
                continue
            for row in rows:
                instrument = _row_to_instrument(row)
                if not instrument:
                    continue
                self._by_symbol[normalize_symbol_key(instrument.trading_symbol)] = instrument
                if instrument.expiry_date:
                    contract_key = (
                        instrument.underlying,
                        instrument.expiry_date.strftime("%Y%m%d"),
                        float(instrument.strike),
                        instrument.option_type,
                    )
                    self._by_contract[contract_key] = instrument
        self._loaded = True

    def resolve(self, symbol: Any, *, underlying: Any = None) -> Optional[UpstoxInstrument]:
        self._load()
        raw = str(symbol or "").strip()
        normalized = normalize_symbol_key(raw)
        if normalized in self._by_symbol:
            return self._by_symbol[normalized]

        # Zerodha monthly index options use YYMMM (for example,
        # NIFTY26JUL24100CE). That shape is ambiguous with DDMMMYY and the
        # generic parser can otherwise read it as 26-Jul-2024, strike 100.
        # Prefer the monthly interpretation only when it resolves to a real
        # contract in the current Upstox master.
        under_hint = normalize_symbol_key(underlying)
        underlying_choices = [under_hint] if under_hint else sorted(SUPPORTED_INDEX_UNDERLYINGS, key=len, reverse=True)
        for under in underlying_choices:
            if not under or not normalized.startswith(under):
                continue
            monthly_match = re.match(r"^(\d{2})([A-Z]{3})(\d+)(CE|PE)$", normalized[len(under):])
            if not monthly_match:
                continue
            year, month_text, strike_text, option_type = monthly_match.groups()
            try:
                month_expiry = datetime.strptime(f"{year}{month_text}", "%y%b")
                strike = float(strike_text)
            except ValueError:
                continue
            month_key = month_expiry.strftime("%Y%m")
            monthly_contracts = [
                instrument
                for key, instrument in self._by_contract.items()
                if key[0] == under
                and key[1].startswith(month_key)
                and key[2] == strike
                and key[3] == option_type
            ]
            if monthly_contracts:
                # The monthly expiry is the last listed expiry for the month.
                return max(monthly_contracts, key=lambda item: item.expiry_date)

        parsed = _parse_option_symbol(raw, underlying=underlying)
        if not parsed:
            return None
        if parsed.get("month_only"):
            month_key = parsed["expiry"].strftime("%Y%m")
            for key, instrument in self._by_contract.items():
                if (
                    key[0] == parsed["underlying"]
                    and key[1].startswith(month_key)
                    and key[2] == float(parsed["strike"])
                    and key[3] == parsed["option_type"]
                ):
                    return instrument
            return None
        contract_key = (
            parsed["underlying"],
            parsed["expiry"].strftime("%Y%m%d"),
            float(parsed["strike"]),
            parsed["option_type"],
        )
        return self._by_contract.get(contract_key)

    def resolve_contract(
        self,
        *,
        underlying: Any,
        expiry_date: Any,
        strike: Any,
        option_type: Any,
    ) -> Optional[UpstoxInstrument]:
        self._load()
        under = normalize_symbol_key(underlying)
        opt = normalize_symbol_key(option_type)
        expiry = _expiry_from_upstox(expiry_date)
        strike_value = _to_float(strike)
        if not (under and opt in {"CE", "PE"} and expiry and strike_value is not None):
            return None
        return self._by_contract.get((under, expiry.strftime("%Y%m%d"), float(strike_value), opt))


def _parse_option_symbol(symbol: Any, *, underlying: Any = None) -> Optional[dict[str, Any]]:
    raw = normalize_symbol_key(symbol)
    if not raw:
        return None
    under_hint = normalize_symbol_key(underlying)
    underlying_choices = [under_hint] if under_hint else sorted(SUPPORTED_INDEX_UNDERLYINGS, key=len, reverse=True)
    for under in underlying_choices:
        if not under or not raw.startswith(under):
            continue
        tail = raw[len(under):]
        if under == "NIFTY":
            weekly_match = re.match(r"^(\d{2})([1-9OND])(\d{2})(\d+)(CE|PE)$", tail)
            if weekly_match:
                year, month_code, day, strike_text, option_type = weekly_match.groups()
                try:
                    expiry = datetime(
                        2000 + int(year),
                        ZERODHA_WEEKLY_MONTH_CODES[month_code],
                        int(day),
                    )
                    strike = float(strike_text)
                except (KeyError, ValueError):
                    pass
                else:
                    return {
                        "underlying": under,
                        "expiry": expiry,
                        "strike": strike,
                        "option_type": option_type,
                        "month_only": False,
                    }
        for fmt in ("%d%b%y", "%y%b%d", "%y%m%d", "%y%b"):
            date_len = {"%d%b%y": 7, "%y%b%d": 7, "%y%m%d": 6, "%y%b": 5}[fmt]
            if len(tail) <= date_len + 2:
                continue
            expiry_part = tail[:date_len]
            rest = tail[date_len:]
            option_type = rest[-2:]
            strike_text = rest[:-2]
            if option_type not in {"CE", "PE"} or not strike_text:
                continue
            try:
                expiry = datetime.strptime(expiry_part.title(), fmt)
                strike = float(strike_text)
            except ValueError:
                continue
            if fmt == "%y%b":
                return {"underlying": under, "expiry": expiry, "strike": strike, "option_type": option_type, "month_only": True}
            return {"underlying": under, "expiry": expiry, "strike": strike, "option_type": option_type, "month_only": False}
    return None


def get_active_option_instruments() -> list[UpstoxInstrument]:
    resolver = UpstoxInstrumentResolver()
    queryset = (
        Tradeorderhistory.objects.filter(transaction_type__iexact="BUY", order_id__isnull=False)
        .filter(date=timezone.localdate())
        .exclude(Q(order_id=0) | Q(trade_order_status__iexact="CLOSE"))
        .order_by("-id")
    )
    instruments: dict[str, UpstoxInstrument] = {}
    for trade in queryset.iterator():
        if str(trade.order_status or "").strip().lower() not in OPEN_ORDER_STATUSES:
            continue
        order_params = trade.order_params if isinstance(trade.order_params, dict) else {}
        metadata = trade.sltp_metadata if isinstance(getattr(trade, "sltp_metadata", None), dict) else {}
        instrument_key = str(metadata.get("instrument_key") or order_params.get("instrument_key") or "").strip()
        if instrument_key:
            instrument = resolver.resolve_contract(
                underlying=metadata.get("underlying") or order_params.get("symbol") or order_params.get("underlying"),
                expiry_date=metadata.get("expiry") or order_params.get("expiry") or _expiry_from_parts(
                    order_params.get("day"),
                    order_params.get("month"),
                    order_params.get("fullyear") or order_params.get("year"),
                ),
                strike=metadata.get("strike") or order_params.get("strike") or order_params.get("strike_price"),
                option_type=metadata.get("option_type") or order_params.get("option_type") or order_params.get("Type"),
            )
            if instrument and instrument.instrument_key == instrument_key:
                instruments[instrument.instrument_key] = instrument
                continue

        instrument = resolver.resolve_contract(
            underlying=metadata.get("underlying") or order_params.get("symbol") or order_params.get("underlying"),
            expiry_date=metadata.get("expiry") or order_params.get("expiry") or _expiry_from_parts(
                order_params.get("day"),
                order_params.get("month"),
                order_params.get("fullyear") or order_params.get("year"),
            ),
            strike=metadata.get("strike") or order_params.get("strike") or order_params.get("strike_price"),
            option_type=metadata.get("option_type") or order_params.get("option_type") or order_params.get("Type"),
        )
        if not instrument:
            instrument = resolver.resolve(trade.trading_symbol or trade.Index_Symbol, underlying=metadata.get("underlying") or order_params.get("symbol"))
        if not instrument:
            instrument = resolver.resolve_contract(
                underlying=order_params.get("symbol") or order_params.get("underlying"),
                expiry_date=order_params.get("expiry") or _expiry_from_parts(
                    order_params.get("day"),
                    order_params.get("month"),
                    order_params.get("fullyear") or order_params.get("year"),
                ),
                strike=order_params.get("strike") or order_params.get("strike_price"),
                option_type=order_params.get("option_type") or order_params.get("Type"),
            )
        if instrument:
            instruments[instrument.instrument_key] = instrument
    return list(instruments.values())


def _expiry_from_parts(day: Any, month: Any, year: Any) -> Optional[str]:
    if not (day and month and year):
        return None
    year_text = str(year).strip()
    if len(year_text) == 2:
        year_text = f"20{year_text}"
    return f"{day}-{month}-{year_text}"


def get_market_data_broker_details() -> Optional[ClientBrokerdetails]:
    dedicated = (
        MarketDataCredential.objects.select_related("execution_node")
        .filter(provider=MarketDataCredential.PROVIDER_UPSTOX, is_active=True)
        .first()
    )
    if dedicated:
        token = get_access_token(dedicated)
        expiry = getattr(dedicated, "access_token_expiry", None)
        if token and (not expiry or expiry > timezone.now()):
            return dedicated

    client_id = str(getattr(settings, "MARKET_DATA_UPSTOX_CLIENT_ID", "") or "").strip()
    queryset = (
        ClientBrokerdetails.objects.select_related("broker_name", "execution_node", "client")
        .filter(broker_name__broker_name__iexact="upstox")
        .order_by("-id")
    )
    if client_id:
        queryset = queryset.filter(Q(client_id=client_id) | Q(broker_API_UID=client_id) | Q(broker_Demate_User_Name=client_id))

    for broker_details in queryset:
        token = get_access_token(broker_details)
        if not token:
            continue
        expiry = getattr(broker_details, "access_token_expiry", None)
        if expiry and expiry <= timezone.now():
            continue
        node = getattr(broker_details, "execution_node", None)
        if not node or not node.is_active or not node.is_verified_with_broker:
            continue
        if node.execution_type == node.EXECUTION_TYPE_PROXY and not node.proxy_public_ip_verified:
            continue
        return broker_details
    return None


def fetch_central_upstox_option_ltp(instrument: UpstoxInstrument) -> Optional[float]:
    cached_payload = get_live_price(instrument_key=instrument.instrument_key, max_age_seconds=5)
    if cached_payload and cached_payload.get("is_fresh"):
        return _to_float(cached_payload.get("ltp"))

    lock_key = f"market-data:on-demand:{normalize_symbol_key(instrument.instrument_key)}"
    has_lock = cache.add(lock_key, "1", timeout=5)
    if not has_lock:
        for _ in range(20):
            time.sleep(0.1)
            cached_payload = get_live_price(instrument_key=instrument.instrument_key, max_age_seconds=10)
            if cached_payload and cached_payload.get("is_fresh"):
                return _to_float(cached_payload.get("ltp"))
        return None

    try:
        credential = get_market_data_broker_details()
        if not credential:
            return None
        access_token = get_access_token(credential)
        if not access_token:
            return None
        node = getattr(credential, "execution_node", None)
        proxies = build_requests_proxy_config(node) if node else None
        request_context = allow_direct_market_data_egress() if not proxies else nullcontext()
        with request_context:
            response = requests.get(
                UPSTOX_MARKET_QUOTE_LTP_URL,
                headers={"Authorization": f"Bearer {access_token}", "Accept": "application/json"},
                params={"instrument_key": instrument.instrument_key},
                timeout=5,
                proxies=proxies,
            )
        payload = response.json() if response.content else {}
        if response.status_code != 200:
            logger.warning(
                "Central Upstox on-demand LTP failed for %s: %s %s",
                instrument.instrument_key,
                response.status_code,
                str(payload)[:200],
            )
            return None
        quote_data = payload.get("data") if isinstance(payload, dict) else None
        quote = next(iter(quote_data.values()), {}) if isinstance(quote_data, dict) else {}
        ltp = _to_float(quote.get("last_price") or quote.get("ltp")) if isinstance(quote, dict) else None
        live_payload = build_live_price_payload(
            instrument_key=instrument.instrument_key,
            ltp=ltp,
            source="upstox-central-rest",
            trading_symbol=instrument.trading_symbol,
            underlying=instrument.underlying,
            expiry_date=instrument.expiry_date,
            strike=instrument.strike,
            option_type=instrument.option_type,
        )
        if not live_payload:
            return None
        cache_live_price(live_payload, aliases=instrument.aliases)
        cache_option_ltp(
            instrument.trading_symbol,
            live_payload["ltp"],
            expiry_date=instrument.expiry_date,
            underlying=instrument.underlying,
            source="upstox-central-rest",
        )
        return live_payload["ltp"]
    except Exception as exc:
        logger.warning("Central Upstox on-demand LTP exception for %s: %s", instrument.instrument_key, exc)
        return None
    finally:
        cache.delete(lock_key)


class UpstoxMarketDataCollector:
    def __init__(self, *, refresh_seconds: Optional[int] = None):
        self.refresh_seconds = refresh_seconds or int(getattr(settings, "MARKET_DATA_SUBSCRIPTION_REFRESH_SECONDS", 30))
        self.api_version = str(getattr(settings, "MARKET_DATA_UPSTOX_API_VERSION", "2.0") or "2.0")
        self.recv_timeout_seconds = int(getattr(settings, "MARKET_DATA_WEBSOCKET_RECV_TIMEOUT_SECONDS", 45))
        self.instruments: dict[str, UpstoxInstrument] = {}
        self.proxy_url: Optional[str] = None
        self.last_tick_at: dict[str, datetime] = {}

    def _decode_protobuf(self, buffer: bytes):
        feed_response = pb.FeedResponse()
        feed_response.ParseFromString(buffer)
        return MessageToDict(feed_response)

    def _authorize_feed(self, broker_details: ClientBrokerdetails):
        token = get_access_token(broker_details)
        version = "v3" if str(self.api_version).startswith("3") else "v2"
        url = f"https://api.upstox.com/{version}/feed/market-data-feed/authorize"
        node = getattr(broker_details, "execution_node", None)
        proxies = build_requests_proxy_config(node) if node else None
        request_context = allow_direct_market_data_egress() if not proxies else nullcontext()
        with request_context:
            response = requests.get(
                url,
                headers={"Authorization": f"Bearer {token}", "Accept": "application/json"},
                timeout=10,
                proxies=proxies,
            )
        payload = response.json() if response.content else {}
        if response.status_code != 200:
            raise RuntimeError(f"Upstox market-data authorize failed: {response.status_code} {str(payload)[:300]}")
        redirect_uri = (payload.get("data") or {}).get("authorized_redirect_uri")
        if not redirect_uri:
            raise RuntimeError(f"Upstox market-data authorize did not return a websocket URL: {str(payload)[:300]}")
        return redirect_uri

    async def _refresh_instruments(self) -> None:
        instruments = await sync_to_async(get_active_option_instruments)()
        self.instruments = {item.instrument_key: item for item in instruments}

    async def _send_subscription(self, websocket, method: str = "sub") -> None:
        keys = list(self.instruments.keys())
        for index in range(0, len(keys), 100):
            chunk = keys[index:index + 100]
            if not chunk:
                continue
            payload = {
                "guid": f"sparkbridge-{method}-{index}",
                "method": method,
                "data": {"mode": "ltpc", "instrumentKeys": chunk},
            }
            await websocket.send(json.dumps(payload).encode("utf-8"))

    def _extract_ltp(self, data: dict[str, Any]) -> tuple[Optional[float], Any]:
        ltpc = data.get("ltpc") or {}
        ff = data.get("ff") or {}
        market_ff = ff.get("marketFF") or {}
        index_ff = ff.get("indexFF") or {}
        oc = data.get("oc") or {}
        ltpc = ltpc or market_ff.get("ltpc") or index_ff.get("ltpc") or oc.get("ltpc") or {}
        return _to_float(ltpc.get("ltp") or ltpc.get("cp")), ltpc.get("ltt")

    async def _process_tick(self, tick_data: dict[str, Any]) -> int:
        feeds = tick_data.get("feeds") or {}
        saved = 0
        for instrument_key, data in feeds.items():
            instrument = self.instruments.get(instrument_key)
            if not instrument:
                continue
            ltp, exchange_ts = self._extract_ltp(data if isinstance(data, dict) else {})
            payload = build_live_price_payload(
                instrument_key=instrument.instrument_key,
                ltp=ltp,
                source="upstox-websocket",
                trading_symbol=instrument.trading_symbol,
                exchange_ts=exchange_ts,
                underlying=instrument.underlying,
                expiry_date=instrument.expiry_date,
                strike=instrument.strike,
                option_type=instrument.option_type,
            )
            if not payload:
                continue
            await sync_to_async(cache_live_price)(payload, aliases=instrument.aliases)
            await sync_to_async(cache_option_ltp)(
                instrument.trading_symbol,
                payload["ltp"],
                expiry_date=instrument.expiry_date,
                underlying=instrument.underlying,
                source="upstox-websocket",
            )
            saved += 1
            self.last_tick_at[instrument.instrument_key] = timezone.now()
        return saved

    async def run_forever(self) -> None:
        while True:
            try:
                await self._run_once()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.exception("Upstox market data collector disconnected; reconnecting shortly: %s", exc)
                await asyncio.sleep(5)

    async def _run_once(self) -> None:
        broker_details = await sync_to_async(get_market_data_broker_details)()
        if not broker_details:
            logger.warning("No active Upstox market-data token is available for market-data collection.")
            await asyncio.sleep(10)
            return

        node = getattr(broker_details, "execution_node", None)
        proxy_config = build_requests_proxy_config(node) if node else {}
        self.proxy_url = proxy_config.get("https") or proxy_config.get("http") or None
        await self._refresh_instruments()
        if not self.instruments:
            logger.info("No open option trades require Upstox market-data subscription.")
            await asyncio.sleep(self.refresh_seconds)
            return

        uri = await sync_to_async(self._authorize_feed)(broker_details)
        ssl_context = ssl.create_default_context()

        logger.info("Connecting Upstox market-data collector for %s instruments.", len(self.instruments))
        async with websockets.connect(
            uri,
            ssl=ssl_context,
            proxy=self.proxy_url,
            max_size=4 * 1024 * 1024,
            ping_interval=20,
            ping_timeout=20,
            close_timeout=10,
        ) as websocket:
            await asyncio.sleep(1)
            await self._send_subscription(websocket, method="sub")
            last_refresh = timezone.now()
            while True:
                if (timezone.now() - last_refresh).total_seconds() >= self.refresh_seconds:
                    old_keys = set(self.instruments.keys())
                    await self._refresh_instruments()
                    new_keys = set(self.instruments.keys())
                    removed = old_keys - new_keys
                    added = new_keys - old_keys
                    if added:
                        await self._send_subscription(websocket, method="sub")
                    if removed:
                        for index in range(0, len(removed), 100):
                            chunk = list(removed)[index:index + 100]
                            payload = {
                                "guid": f"sparkbridge-unsub-{index}",
                                "method": "unsub",
                                "data": {"instrumentKeys": chunk},
                            }
                            await websocket.send(json.dumps(payload).encode("utf-8"))
                    last_refresh = timezone.now()

                message = await asyncio.wait_for(websocket.recv(), timeout=self.recv_timeout_seconds)
                decoded = self._decode_protobuf(message)
                saved = await self._process_tick(decoded)
                if saved:
                    logger.debug("Cached %s live Upstox ticks.", saved)
