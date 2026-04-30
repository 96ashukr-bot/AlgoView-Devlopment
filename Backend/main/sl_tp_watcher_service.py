from __future__ import annotations

import time
from dataclasses import dataclass
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

SUCCESS_EXIT_STATUSES = {"complete", "completed", "open"}


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
            entry_price=self._to_float(trade_order.Entry_Price) or self._to_float(trade_order.LivePrice),
            quantity=quantity,
            trigger_reason=trigger_reason,
            response=response,
        )

    def __init__(self):
        self._contract_manager = ContractMasterManager.get_instance()
        self._symbol_parser = get_symbol_parser()
        self._execution_engine = get_execution_engine()

    @staticmethod
    def _to_float(value: Any) -> Optional[float]:
        if value in (None, "", "None"):
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

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

    def _get_current_ltp(self, trade_order: Tradeorderhistory, broker_details: ClientBrokerdetails) -> Optional[float]:
        trading_symbol = str(trade_order.trading_symbol or "").strip().upper()
        if not trading_symbol:
            return None

        self._contract_manager.initialize(blocking=True)
        contract = next(iter(self._contract_manager.get_contracts_by_symbol(trading_symbol)), None)
        if contract:
            ltp = get_ltp(
                symbol_token=contract.token,
                exchange=contract.exchange or trade_order.Exchange or "NFO",
                tradingsymbol=contract.symbol,
                broker_details=broker_details,
            )
            return ltp or None

        parsed = self._symbol_parser.parse(trading_symbol)
        if not parsed.is_option:
            return None

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
            return None

        ltp = get_ltp(
            symbol_token=contract.token,
            exchange=contract.exchange or trade_order.Exchange or "NFO",
            tradingsymbol=contract.symbol,
            broker_details=broker_details,
        )
        return ltp or None

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
        if not parsed.is_option:
            raise ValueError(f"Trading symbol '{trade_order.trading_symbol}' is not a supported option symbol")

        expiry = parsed.expiry_date or getattr(trade_setting, "expiry_date", None)
        if not expiry:
            raise ValueError("Expiry could not be resolved for auto-exit")

        return ExecutionRequest(
            LivePrice=current_ltp,
            group_service=trade_order.GroupService,
            trade=trade_setting,
            user=trade_order.client,
            transaction_type="SELL",
            symbol=parsed.underlying,
            quantity=int(self._to_float(trade_order.EntryQty) or self._to_float(trade_setting.quantity) or 0),
            strategy=trade_order.strategy or trade_setting.strategy,
            ordertype=(trade_setting.order_type or "LIMIT"),
            product_type=trade_setting.product_type or trade_order.order_params.get("product_type"),
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
                "original_history_id": trade_order.history_id,
            },
            Exchange=trade_order.Exchange or "NFO",
            Segment=trade_order.Segment,
            Index_Symbol=trade_order.Index_Symbol,
            triggerPrice=stop_loss_price if trigger_reason == "STOP_LOSS" else target_price,
            day=expiry.strftime("%d"),
            month=expiry.strftime("%b").upper(),
            year=expiry.strftime("%y"),
            fullyear=expiry.strftime("%Y"),
            strike=parsed.strike,
            option_type=parsed.option_type,
            order_params={
                "trigger_source": "sl_tp_watcher",
                "trigger_reason": trigger_reason,
                "current_ltp": current_ltp,
                "effective_stop_loss_price": stop_loss_price,
                "effective_target_price": target_price,
            },
            history_id=trade_order.history_id,
        )

    def _try_acquire_lock(self, trade_order: Tradeorderhistory) -> bool:
        lock_key = f"sl_tp_watcher_lock:{trade_order.history_id or trade_order.id}"
        return cache.add(lock_key, "1", timeout=self.LOCK_TIMEOUT_SECONDS)

    def _release_lock(self, trade_order: Tradeorderhistory) -> None:
        lock_key = f"sl_tp_watcher_lock:{trade_order.history_id or trade_order.id}"
        cache.delete(lock_key)

    def process_trade(self, trade_order: Tradeorderhistory, execute_exit: bool = True) -> WatchResult:
        broker = str(trade_order.broker or "").strip()
        if broker.lower() not in {"angel one", "angle one"}:
            return self._build_watch_result(
                trade_order,
                status="skipped",
                message=f"Broker '{broker}' is not supported by the watcher yet.",
            )

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

        current_ltp = self._get_current_ltp(trade_order, broker_details)
        if current_ltp is None or current_ltp <= 0:
            return self._build_watch_result(
                trade_order,
                status="skipped",
                message="Live price could not be fetched.",
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
