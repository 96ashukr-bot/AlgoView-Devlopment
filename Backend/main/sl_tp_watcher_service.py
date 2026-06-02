from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.db.models import Q
from django.utils import timezone

from main.angleapi_upgraded import get_ltp
from main.angelone.managers.contract_manager import ContractMasterManager
from main.angelone.utils.logging_utils import TradingLogger
from main.angelone.utils.symbol_parser import get_symbol_parser
from main.execution_engine import ExecutionRequest, get_execution_engine
from main.models import ClientBrokerdetails, ClientTradeSetting, Tradeorderhistory
from main.services.live_price_cache import get_live_price
from main.services.upstox_market_data import UpstoxInstrumentResolver

logger = TradingLogger("sl_tp_watcher")


OPEN_ORDER_STATUSES = {
    "complete",
    "completed",
    "open",
    "pending",
    "put order req received",
    "traded",
    "transit",
}

SUCCESS_EXIT_STATUSES = {"complete", "completed", "success", "open", "placed"}


@dataclass
class WatchResult:
    trade_id: int
    client_id: int
    client_name: Optional[str]
    broker: str
    symbol: str
    trading_symbol: Optional[str]
    group_service: Optional[str]
    script_name: Optional[str]
    status: str
    message: str
    current_ltp: Optional[float] = None
    stop_loss_price: Optional[float] = None
    target_price: Optional[float] = None
    entry_price: Optional[float] = None
    quantity: Optional[int] = None
    trigger_reason: Optional[str] = None
    response: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        payload = {
            "trade_id": self.trade_id,
            "client_id": self.client_id,
            "client_name": self.client_name,
            "broker": self.broker,
            "symbol": self.symbol,
            "trading_symbol": self.trading_symbol,
            "group_service": self.group_service,
            "script_name": self.script_name,
            "status": self.status,
            "message": self.message,
            "current_ltp": self.current_ltp,
            "stop_loss_price": self.stop_loss_price,
            "target_price": self.target_price,
            "entry_price": self.entry_price,
            "quantity": self.quantity,
            "trigger_reason": self.trigger_reason,
        }
        if self.response is not None:
            payload["response"] = self.response
        return payload


class SLTPWatcherService:
    LOCK_TIMEOUT_SECONDS = 30
    EXIT_FAILURE_COOLDOWN_SECONDS = 60
    RATE_LIMIT_COOLDOWN_SECONDS = 180
    EMPTY_RESPONSE_COOLDOWN_SECONDS = 120

    @staticmethod
    def _build_watch_result(
        trade_order: Tradeorderhistory,
        status: str,
        message: str,
        *,
        current_ltp: Optional[float] = None,
        stop_loss_price: Optional[float] = None,
        target_price: Optional[float] = None,
        trigger_reason: Optional[str] = None,
        response: Optional[Dict[str, Any]] = None,
    ) -> WatchResult:
        client_name = getattr(trade_order.client, "fullName", None) or getattr(trade_order.client, "userName", None)
        quantity_value = trade_order.EntryQty or trade_order.ExitQty
        try:
            quantity = int(float(quantity_value)) if quantity_value not in (None, "", "None") else None
        except (TypeError, ValueError):
            quantity = None

        return WatchResult(
            trade_id=trade_order.id,
            client_id=trade_order.client_id,
            client_name=client_name,
            broker=str(trade_order.broker or "").strip(),
            symbol=str(trade_order.Index_Symbol or trade_order.trading_symbol or ""),
            trading_symbol=str(trade_order.trading_symbol or ""),
            group_service=str(trade_order.GroupService or ""),
            script_name=str(trade_order.Index_Symbol or trade_order.trading_symbol or ""),
            status=status,
            message=message,
            current_ltp=current_ltp,
            stop_loss_price=stop_loss_price,
            target_price=target_price,
            entry_price=SLTPWatcherService._to_float(trade_order.Entry_Price) or SLTPWatcherService._to_float(trade_order.LivePrice),
            quantity=quantity,
            trigger_reason=trigger_reason,
            response=response,
        )

    def __init__(self):
        self._contract_manager = ContractMasterManager.get_instance()
        self._symbol_parser = get_symbol_parser()
        self._execution_engine = get_execution_engine()
        self._upstox_resolver = UpstoxInstrumentResolver()

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _looks_like_option_symbol(value: Any) -> bool:
        text = str(value or "").strip().upper()
        return len(text) > 6 and ("CE" in text or "PE" in text)

    @classmethod
    def _has_option_contract_metadata(cls, trade_order: Tradeorderhistory) -> bool:
        order_params = trade_order.order_params if isinstance(trade_order.order_params, dict) else {}
        option_type = str(order_params.get("option_type") or order_params.get("Type") or "").strip().upper()
        has_metadata = bool(
            (order_params.get("symbol") or order_params.get("underlying"))
            and (order_params.get("strike") or order_params.get("strike_price"))
            and option_type in {"CE", "PE"}
        )
        return has_metadata or cls._looks_like_option_symbol(trade_order.trading_symbol) or cls._looks_like_option_symbol(trade_order.Index_Symbol)

    @classmethod
    def _payload_matches_option_contract(cls, trade_order: Tradeorderhistory, payload: Dict[str, Any]) -> bool:
        option_type = str(payload.get("option_type") or "").strip().upper()
        if option_type not in {"CE", "PE"}:
            return False

        payload_strike = cls._to_float(payload.get("strike"))
        if payload_strike is None:
            return False

        order_params = trade_order.order_params if isinstance(trade_order.order_params, dict) else {}
        expected_option_type = str(order_params.get("option_type") or order_params.get("Type") or "").strip().upper()
        if expected_option_type in {"CE", "PE"} and option_type != expected_option_type:
            return False

        expected_strike = cls._to_float(order_params.get("strike") or order_params.get("strike_price"))
        if expected_strike is not None and abs(payload_strike - expected_strike) > 0.001:
            return False

        expected_underlying = str(order_params.get("symbol") or order_params.get("underlying") or "").replace(" ", "").upper()
        payload_underlying = str(payload.get("underlying") or "").replace(" ", "").upper()
        if expected_underlying and payload_underlying and payload_underlying != expected_underlying:
            return False

        return True

    @staticmethod
    def _normalize_sl_tp_type(value: Any) -> Optional[str]:
        if value in (None, "", "None"):
            return None
        normalized = str(value).strip().upper()
        if normalized in {"%", "PERCENT", "PERCENTAGE"}:
            return "PERCENTAGE"
        if normalized in {"POINT", "POINTS"}:
            return "POINTS"
        return None

    def _get_open_trades(self):
        queryset = Tradeorderhistory.objects.select_related("client").filter(
            transaction_type__iexact="BUY",
            order_id__isnull=False,
            date=timezone.localdate(),
        ).exclude(
            Q(order_id=0) | Q(trade_order_status__iexact="CLOSE")
        ).order_by("-id")
        eligible_ids = [
            item.id
            for item in queryset
            if str(item.order_status or "").strip().lower() in OPEN_ORDER_STATUSES
        ]
        return Tradeorderhistory.objects.select_related("client").filter(id__in=eligible_ids).order_by("-id")

    def _find_trade_setting(self, trade_order: Tradeorderhistory) -> Optional[ClientTradeSetting]:
        base_queryset = ClientTradeSetting.objects.select_related("segment", "sub_segment").filter(
            client=trade_order.client,
            group_service=trade_order.GroupService,
        )
        symbol = str(trade_order.Index_Symbol or "").strip()
        if symbol:
            trade_setting = base_queryset.filter(
                Q(symbol__iexact=symbol)
                | Q(sub_segment__name__iexact=symbol)
                | Q(sub_segment__short_name__iexact=symbol)
            ).first()
            if trade_setting:
                return trade_setting
        return base_queryset.first()

    def _get_broker_details(self, trade_setting: ClientTradeSetting) -> Optional[ClientBrokerdetails]:
        broker_name = str(getattr(trade_setting, "broker", "") or "").strip()
        if not broker_name:
            return None
        return ClientBrokerdetails.objects.filter(
            client=trade_setting.client,
            broker_name__broker_name__iexact=broker_name,
        ).select_related("broker_name").first()

    def _resolve_market_instrument(self, trade_order: Tradeorderhistory):
        order_params = trade_order.order_params if isinstance(trade_order.order_params, dict) else {}
        expiry = order_params.get("expiry")
        if not expiry and order_params.get("day") and order_params.get("month"):
            year = str(order_params.get("fullyear") or order_params.get("year") or "")
            if len(year) == 2:
                year = f"20{year}"
            if year:
                expiry = f"{order_params.get('day')}-{order_params.get('month')}-{year}"

        instrument = self._upstox_resolver.resolve_contract(
            underlying=order_params.get("symbol") or order_params.get("underlying"),
            expiry_date=expiry,
            strike=order_params.get("strike") or order_params.get("strike_price"),
            option_type=order_params.get("option_type") or order_params.get("Type"),
        )
        if instrument:
            return instrument

        for symbol in (trade_order.trading_symbol, trade_order.Index_Symbol):
            if not self._looks_like_option_symbol(symbol):
                continue
            instrument = self._upstox_resolver.resolve(
                symbol,
                underlying=order_params.get("symbol") or order_params.get("underlying"),
            )
            if instrument:
                return instrument
        return None

    def _get_cached_current_ltp(self, trade_order: Tradeorderhistory) -> tuple[Optional[float], Optional[str]]:
        instrument = self._resolve_market_instrument(trade_order)
        is_option_trade = self._has_option_contract_metadata(trade_order)
        payload = None
        if instrument:
            payload = get_live_price(instrument_key=instrument.instrument_key)
        if not payload and not is_option_trade:
            payload = get_live_price(trading_symbol=trade_order.trading_symbol)
        if not payload and instrument:
            payload = get_live_price(
                underlying=instrument.underlying,
                expiry_date=instrument.expiry_date,
                strike=instrument.strike,
                option_type=instrument.option_type,
            )
        if not payload:
            if is_option_trade:
                return None, "Option live price is not available in the central cache."
            return None, "Live price is not available in the central cache."
        if not payload.get("is_fresh"):
            age = payload.get("age_seconds")
            age_text = f" Age: {age}s." if age is not None else ""
            return None, f"Live price is stale.{age_text}"
        if is_option_trade and not self._payload_matches_option_contract(trade_order, payload):
            return None, "Cached live price does not match the option contract."
        ltp = self._to_float(payload.get("ltp"))
        if ltp is None or ltp <= 0:
            return None, "Cached live price is invalid."
        return ltp, None

    def _get_current_ltp(self, trade_order: Tradeorderhistory, broker_details: ClientBrokerdetails) -> tuple[Optional[float], Optional[str]]:
        cached_ltp, cache_error = self._get_cached_current_ltp(trade_order)
        if cached_ltp is not None:
            return cached_ltp, None

        trading_symbol = str(trade_order.trading_symbol or "").strip().upper()
        if not trading_symbol:
            return None, cache_error or "Trading symbol is missing."

        if self._has_option_contract_metadata(trade_order) and not self._looks_like_option_symbol(trading_symbol):
            return None, cache_error or "Option trading symbol is missing."

        broker = str(trade_order.broker or "").strip().lower()
        if broker not in {"angel one", "angle one"}:
            return None, cache_error

        self._contract_manager.initialize(blocking=True)
        contract = next(iter(self._contract_manager.get_contracts_by_symbol(trading_symbol)), None)
        if contract:
            ltp = get_ltp(
                symbol_token=contract.token,
                exchange=contract.exchange or trade_order.Exchange or "NFO",
                tradingsymbol=contract.symbol,
                broker_details=broker_details,
            )
            return ltp or None, None if ltp else cache_error

        parsed = self._symbol_parser.parse(trading_symbol)
        if not parsed.is_option:
            return None, cache_error

        expiry = parsed.expiry_date
        contract, _resolution = self._contract_manager.resolve_option_contract(
            underlying=parsed.underlying,
            strike=float(parsed.strike),
            option_type=parsed.option_type,
            exchange=trade_order.Exchange or "NFO",
            expiry=expiry,
            prefer_weekly=True,
        )
        if not contract:
            return None, cache_error

        ltp = get_ltp(
            symbol_token=contract.token,
            exchange=contract.exchange or trade_order.Exchange or "NFO",
            tradingsymbol=contract.symbol,
            broker_details=broker_details,
        )
        return ltp or None, None if ltp else cache_error

    def _resolve_thresholds(
        self,
        trade_order: Tradeorderhistory,
        trade_setting: ClientTradeSetting,
    ) -> Dict[str, Optional[float]]:
        order_params = trade_order.order_params if isinstance(trade_order.order_params, dict) else {}

        stop_loss_price = self._to_float(order_params.get("effective_stop_loss_price"))
        target_price = self._to_float(order_params.get("effective_target_price"))

        if stop_loss_price is not None or target_price is not None:
            return {
                "stop_loss_price": stop_loss_price,
                "target_price": target_price,
                "entry_reference_price": self._to_float(order_params.get("entry_reference_price")) or self._to_float(trade_order.Entry_Price) or self._to_float(trade_order.LivePrice),
            }

        sl_tp_type = self._normalize_sl_tp_type(getattr(trade_setting, "sl_type", None))
        stop_loss_value = self._to_float(getattr(trade_setting, "stop_loss", None))
        target_value = self._to_float(getattr(trade_setting, "target", None))
        entry_price = self._to_float(trade_order.Entry_Price) or self._to_float(trade_order.LivePrice)

        if not sl_tp_type or entry_price is None or entry_price <= 0:
            return {"stop_loss_price": None, "target_price": None, "entry_reference_price": entry_price}

        if stop_loss_value is not None:
            if sl_tp_type == "PERCENTAGE":
                stop_loss_price = round(entry_price * (1 - (stop_loss_value / 100.0)), 2)
            else:
                stop_loss_price = round(entry_price - stop_loss_value, 2)

        if target_value is not None:
            if sl_tp_type == "PERCENTAGE":
                target_price = round(entry_price * (1 + (target_value / 100.0)), 2)
            else:
                target_price = round(entry_price + target_value, 2)

        return {
            "stop_loss_price": stop_loss_price,
            "target_price": target_price,
            "entry_reference_price": entry_price,
        }

    @staticmethod
    def _determine_trigger_reason(current_ltp: float, stop_loss_price: Optional[float], target_price: Optional[float]) -> Optional[str]:
        if stop_loss_price is not None and current_ltp <= stop_loss_price:
            return "STOP_LOSS"
        if target_price is not None and current_ltp >= target_price:
            return "TARGET"
        return None

    def _build_exit_request(
        self,
        trade_order: Tradeorderhistory,
        trade_setting: ClientTradeSetting,
        current_ltp: float,
        trigger_reason: str,
        stop_loss_price: Optional[float],
        target_price: Optional[float],
    ) -> ExecutionRequest:
        parsed = self._symbol_parser.parse(str(trade_order.trading_symbol or ""))
        order_params = trade_order.order_params if isinstance(trade_order.order_params, dict) else {}
        market_instrument = None
        if not parsed.is_option:
            market_instrument = self._resolve_market_instrument(trade_order)
            if not market_instrument:
                raise ValueError(f"Trading symbol '{trade_order.trading_symbol}' is not a supported option symbol")

        expiry = self._expiry_from_order_params(order_params)
        if expiry is None and parsed.is_option and parsed.expiry_str:
            expiry = parsed.expiry_date
        expiry = expiry or getattr(market_instrument, "expiry_date", None) or getattr(trade_setting, "expiry_date", None)
        if not expiry:
            raise ValueError("Expiry could not be resolved for auto-exit")
        underlying = str(order_params.get("symbol") or (parsed.underlying if parsed.is_option else market_instrument.underlying)).upper()
        strike = order_params.get("strike") or order_params.get("strike_price") or (parsed.strike if parsed.is_option else market_instrument.strike)
        option_type = str(order_params.get("option_type") or order_params.get("Type") or (parsed.option_type if parsed.is_option else market_instrument.option_type)).upper()
        original_history_id = str(trade_order.history_id or trade_order.id)
        exit_history_id = f"{original_history_id}_sltp_exit"

        return ExecutionRequest(
            LivePrice=current_ltp,
            group_service=trade_order.GroupService,
            trade=trade_setting,
            user=trade_order.client,
            transaction_type="SELL",
            symbol=underlying,
            quantity=int(self._to_float(trade_order.EntryQty) or self._to_float(trade_setting.quantity) or 0),
            strategy=trade_order.strategy or trade_setting.strategy,
            ordertype=(trade_setting.order_type or "LIMIT"),
            product_type=trade_setting.product_type or (trade_order.order_params or {}).get("product_type"),
            price=None,
            Lots=trade_order.Lot or 1,
            trade_order_status="CLOSE",
            Entry_type=trade_order.Entry_type,
            Exit_type=f"AUTO_{trigger_reason}",
            Entry_price=trade_order.Entry_Price,
            Exit_price=current_ltp,
            EntryQty=trade_order.EntryQty,
            ExitQty=int(self._to_float(trade_order.EntryQty) or self._to_float(trade_setting.quantity) or 0),
            webhook_signal={
                "trigger_source": "sl_tp_watcher",
                "trigger_reason": trigger_reason,
                "current_ltp": current_ltp,
                "stop_loss_price": stop_loss_price,
                "target_price": target_price,
                "triggered_at": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "original_history_id": original_history_id,
            },
            Exchange=trade_order.Exchange or "NFO",
            Segment=trade_order.Segment,
            Index_Symbol=trade_order.Index_Symbol,
            triggerPrice=stop_loss_price if trigger_reason == "STOP_LOSS" else target_price,
            day=expiry.strftime("%d"),
            month=expiry.strftime("%b").upper(),
            year=expiry.strftime("%y"),
            fullyear=expiry.strftime("%Y"),
            strike=strike,
            option_type=option_type,
            order_params={
                "trigger_source": "sl_tp_watcher",
                "trigger_reason": trigger_reason,
                "current_ltp": current_ltp,
                "effective_stop_loss_price": stop_loss_price,
                "effective_target_price": target_price,
            },
            history_id=exit_history_id,
        )

    @staticmethod
    def _expiry_from_order_params(order_params: Dict[str, Any]) -> Optional[datetime]:
        expiry = order_params.get("expiry") or order_params.get("expiry_date")
        if expiry:
            for date_format in ("%Y-%m-%d", "%d-%b-%Y", "%d%b%Y", "%d%b%y"):
                try:
                    return datetime.strptime(str(expiry), date_format)
                except ValueError:
                    continue

        day = order_params.get("day")
        month = order_params.get("month")
        year = order_params.get("fullyear") or order_params.get("year")
        if day and month and year:
            year_text = str(year)
            if len(year_text) == 2:
                year_text = f"20{year_text}"
            try:
                return datetime.strptime(f"{int(float(day)):02d}{str(month)[:3].upper()}{year_text}", "%d%b%Y")
            except (TypeError, ValueError):
                return None
        return None

    def _try_acquire_lock(self, trade_order: Tradeorderhistory) -> bool:
        lock_key = f"sl_tp_watcher_lock:{trade_order.history_id or trade_order.id}"
        return cache.add(lock_key, "1", timeout=self.LOCK_TIMEOUT_SECONDS)

    def _release_lock(self, trade_order: Tradeorderhistory) -> None:
        lock_key = f"sl_tp_watcher_lock:{trade_order.history_id or trade_order.id}"
        cache.delete(lock_key)

    def _exit_cooldown_key(self, trade_order: Tradeorderhistory) -> str:
        return f"sl_tp_watcher_exit_cooldown:{trade_order.history_id or trade_order.id}"

    def _get_exit_cooldown_remaining(self, trade_order: Tradeorderhistory) -> Optional[int]:
        blocked_until = cache.get(self._exit_cooldown_key(trade_order))
        if not blocked_until:
            return None
        remaining = int(round(float(blocked_until) - time.time()))
        if remaining <= 0:
            cache.delete(self._exit_cooldown_key(trade_order))
            return None
        return remaining

    def _cooldown_seconds_for_response(self, response: Dict[str, Any]) -> int:
        data = response.get("data") if isinstance(response, dict) else {}
        message = str((data or {}).get("message") or "").lower()
        error_code = str((data or {}).get("error_code") or "").upper()
        if "access rate" in message or "rate limit" in message or "too many requests" in message:
            return self.RATE_LIMIT_COOLDOWN_SECONDS
        if "empty response" in message or error_code == "EMPTY_BROKER_RESPONSE":
            return self.EMPTY_RESPONSE_COOLDOWN_SECONDS
        return self.EXIT_FAILURE_COOLDOWN_SECONDS

    def _set_exit_cooldown(self, trade_order: Tradeorderhistory, response: Dict[str, Any]) -> int:
        cooldown_seconds = self._cooldown_seconds_for_response(response)
        cache.set(
            self._exit_cooldown_key(trade_order),
            time.time() + cooldown_seconds,
            timeout=cooldown_seconds,
        )
        return cooldown_seconds

    def process_trade(self, trade_order: Tradeorderhistory, execute_exit: bool = True) -> WatchResult:
        trade_setting = self._find_trade_setting(trade_order)
        if not trade_setting:
            return self._build_watch_result(
                trade_order,
                status="skipped",
                message="Matching client trade setting not found.",
            )

        broker_details = self._get_broker_details(trade_setting)
        if not broker_details:
            return self._build_watch_result(
                trade_order,
                status="skipped",
                message="Broker details are missing for the client.",
            )

        thresholds = self._resolve_thresholds(trade_order, trade_setting)
        stop_loss_price = thresholds.get("stop_loss_price")
        target_price = thresholds.get("target_price")
        if stop_loss_price is None and target_price is None:
            return self._build_watch_result(
                trade_order,
                status="skipped",
                message="No active stop-loss or target is configured.",
            )

        current_ltp, ltp_error = self._get_current_ltp(trade_order, broker_details)
        if current_ltp is None or current_ltp <= 0:
            return self._build_watch_result(
                trade_order,
                status="skipped",
                message=ltp_error or "Live price could not be fetched.",
                current_ltp=current_ltp,
                stop_loss_price=stop_loss_price,
                target_price=target_price,
            )

        trigger_reason = self._determine_trigger_reason(current_ltp, stop_loss_price, target_price)
        if not trigger_reason:
            return self._build_watch_result(
                trade_order,
                status="monitoring",
                message="Trade is still within SL/TP bounds.",
                current_ltp=current_ltp,
                stop_loss_price=stop_loss_price,
                target_price=target_price,
            )

        if not execute_exit:
            return self._build_watch_result(
                trade_order,
                status="triggered",
                message=f"{trigger_reason} has been hit. Exit is pending watcher execution.",
                current_ltp=current_ltp,
                stop_loss_price=stop_loss_price,
                target_price=target_price,
                trigger_reason=trigger_reason,
            )

        cooldown_remaining = self._get_exit_cooldown_remaining(trade_order)
        if cooldown_remaining:
            return self._build_watch_result(
                trade_order,
                status="skipped",
                message=f"Previous auto-exit attempt failed recently. Retrying after {cooldown_remaining} seconds.",
                current_ltp=current_ltp,
                stop_loss_price=stop_loss_price,
                target_price=target_price,
                trigger_reason=trigger_reason,
            )

        if not self._try_acquire_lock(trade_order):
            return self._build_watch_result(
                trade_order,
                status="skipped",
                message="Another watcher process is already handling this trade.",
                current_ltp=current_ltp,
                stop_loss_price=stop_loss_price,
                target_price=target_price,
                trigger_reason=trigger_reason,
            )

        try:
            request = self._build_exit_request(
                trade_order=trade_order,
                trade_setting=trade_setting,
                current_ltp=current_ltp,
                trigger_reason=trigger_reason,
                stop_loss_price=stop_loss_price,
                target_price=target_price,
            )
            response = self._execution_engine.execute_order(request)
            response_status = str(response.get("data", {}).get("status", "") or "").lower()

            if response_status in SUCCESS_EXIT_STATUSES:
                trade_order.trade_order_status = "CLOSE"
                trade_order.Exit_status = response.get("data", {}).get("status")
                trade_order.Exit_Price = current_ltp
                trade_order.SignalExit_time = trade_order.SignalExit_time or timezone.now()
                trade_order.save(update_fields=["trade_order_status", "Exit_status", "Exit_Price", "SignalExit_time"])
                message = f"Auto-exit triggered by {trigger_reason}."
                status = "triggered"
            else:
                message = response.get("data", {}).get("message", "Auto-exit request failed.")
                cooldown_seconds = self._set_exit_cooldown(trade_order, response)
                message = f"{message} Auto-exit retry paused for {cooldown_seconds} seconds."
                status = "failed"

            return self._build_watch_result(
                trade_order,
                status=status,
                message=message,
                current_ltp=current_ltp,
                stop_loss_price=stop_loss_price,
                target_price=target_price,
                trigger_reason=trigger_reason,
                response=response,
            )
        finally:
            self._release_lock(trade_order)

    def scan(self, client_id: Optional[int] = None, history_id: Optional[str] = None, execute_exit: bool = True) -> Dict[str, Any]:
        queryset = self._get_open_trades()
        if client_id:
            queryset = queryset.filter(client_id=client_id)
        if history_id:
            queryset = queryset.filter(history_id=history_id)

        results: List[WatchResult] = []
        for trade_order in queryset:
            try:
                results.append(self.process_trade(trade_order, execute_exit=execute_exit))
            except Exception as exc:
                logger.exception(
                    "SL/TP watcher failed while processing trade",
                    trade_id=trade_order.id,
                    client_id=trade_order.client_id,
                    broker=trade_order.broker,
                    error=str(exc),
                )
                results.append(
                    self._build_watch_result(
                        trade_order,
                        status="failed",
                        message=str(exc),
                    )
                )

        summary = {
            "total": len(results),
            "triggered": sum(1 for item in results if item.status == "triggered"),
            "monitoring": sum(1 for item in results if item.status == "monitoring"),
            "skipped": sum(1 for item in results if item.status == "skipped"),
            "failed": sum(1 for item in results if item.status == "failed"),
        }

        return {
            "summary": summary,
            "results": [item.to_dict() for item in results],
        }


_sl_tp_watcher_service: Optional[SLTPWatcherService] = None


def get_sl_tp_watcher_service() -> SLTPWatcherService:
    global _sl_tp_watcher_service
    if _sl_tp_watcher_service is None:
        _sl_tp_watcher_service = SLTPWatcherService()
    return _sl_tp_watcher_service
