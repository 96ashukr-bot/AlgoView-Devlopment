"""
Centralized execution risk controls for webhook-driven trading.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional, Dict, Any

from django.core.cache import cache
from django.utils import timezone

from main.services.trade_limit import (
    complete_successful_buy_slot,
    release_successful_buy_slot,
    reserve_successful_buy_slot,
    successful_buy_count,
)
from main.angelone.constants import (
    DEFAULT_MAX_DAILY_TRADES_PER_CLIENT,
    DEFAULT_MAX_QUANTITY_PER_TRADE,
    DUPLICATE_ORDER_WINDOW_SECONDS,
    MAX_ORDERS_PER_MINUTE_PER_CLIENT,
)
from main.angelone.utils.logging_utils import TradingLogger

logger = TradingLogger("risk_manager")


@dataclass(frozen=True)
class RiskCheckResult:
    allowed: bool
    message: str = ""
    error_code: Optional[str] = None
    reservation_key: Optional[str] = None
    trade_limit_reservation_key: Optional[str] = None


class RiskManager:
    """Thread-safe risk validation backed by Django cache primitives."""

    def validate_and_reserve(self, request) -> RiskCheckResult:
        client_id = getattr(getattr(request, "user", None), "id", None)
        symbol = str(getattr(request, "symbol", "") or "").upper()
        transaction_type = str(getattr(request, "transaction_type", "") or "").upper()
        option_type = str(getattr(request, "option_type", "") or "").upper()
        strike = getattr(request, "strike", None)

        try:
            quantity = int(getattr(request, "quantity", 0) or 0)
        except (TypeError, ValueError):
            quantity = 0

        if not client_id:
            return RiskCheckResult(False, "Client context is required.", "INVALID_CLIENT")
        if not symbol:
            return RiskCheckResult(False, "Symbol is required.", "INVALID_SYMBOL")
        if quantity <= 0:
            return RiskCheckResult(False, "Quantity must be greater than zero.", "INVALID_QUANTITY")

        if self._is_forced_squareoff_exit(request, transaction_type):
            logger.info(
                "Forced squareoff exit bypassed entry risk gates",
                user_id=client_id,
                symbol=symbol,
                strike=strike,
                transaction_type=transaction_type,
                request_id=getattr(request, "request_id", None),
            )
            return RiskCheckResult(True)

        configured_max_quantity = int(
            getattr(getattr(request, "trade", None), "quantity", 0)
            or DEFAULT_MAX_QUANTITY_PER_TRADE
        )
        if quantity > configured_max_quantity:
            return RiskCheckResult(
                False,
                f"Requested quantity {quantity} exceeds this client's configured max quantity {configured_max_quantity}.",
                "MAX_QUANTITY_EXCEEDED",
            )

        if transaction_type == "BUY":
            configured_limit = getattr(getattr(request, "trade", None), "trade_limit", None)
            daily_limit = int(configured_limit or DEFAULT_MAX_DAILY_TRADES_PER_CLIENT)
            daily_trade_count = successful_buy_count(request.user, symbol)
            if daily_trade_count >= daily_limit:
                return RiskCheckResult(
                    False,
                    f"Daily successful BUY trade limit reached ({daily_trade_count}/{daily_limit}) for this client and symbol.",
                    "DAILY_TRADE_LIMIT_REACHED",
                )
            trade_limit_reservation_key = reserve_successful_buy_slot(
                request.user,
                symbol,
                daily_limit,
                request_id=getattr(request, "request_id", None),
            )
            if not trade_limit_reservation_key:
                return RiskCheckResult(
                    False,
                    f"Daily successful BUY trade limit reached ({daily_trade_count}/{daily_limit}) for this client and symbol.",
                    "DAILY_TRADE_LIMIT_REACHED",
                )
        else:
            trade_limit_reservation_key = None

        minute_key = f"risk:minute:{client_id}:{timezone.now().strftime('%Y%m%d%H%M')}"
        cache.add(minute_key, 0, timeout=60)
        try:
            minute_count = cache.incr(minute_key)
        except Exception:
            minute_count = int(cache.get(minute_key, 0) or 0) + 1
            cache.set(minute_key, minute_count, timeout=60)

        if minute_count > MAX_ORDERS_PER_MINUTE_PER_CLIENT:
            release_successful_buy_slot(trade_limit_reservation_key)
            return RiskCheckResult(
                False,
                "Per-minute order rate limit exceeded for this client.",
                "RATE_LIMIT_EXCEEDED",
            )

        duplicate_key = self._duplicate_key(client_id, symbol, strike, option_type, transaction_type)
        reserved = cache.add(
            duplicate_key,
            {"request_id": getattr(request, "request_id", None), "created_at": timezone.now().isoformat()},
            timeout=DUPLICATE_ORDER_WINDOW_SECONDS,
        )
        if not reserved:
            release_successful_buy_slot(trade_limit_reservation_key)
            return RiskCheckResult(
                False,
                "Duplicate trade signal blocked within the protection window.",
                "DUPLICATE_SIGNAL",
            )

        logger.info(
            "Risk checks passed",
            user_id=client_id,
            symbol=symbol,
            strike=strike,
            transaction_type=transaction_type,
            request_id=getattr(request, "request_id", None),
        )
        return RiskCheckResult(
            True,
            reservation_key=duplicate_key,
            trade_limit_reservation_key=trade_limit_reservation_key,
        )

    @staticmethod
    def _is_forced_squareoff_exit(request, transaction_type: str) -> bool:
        if transaction_type != "SELL":
            return False
        order_params = getattr(request, "order_params", None)
        webhook_signal = getattr(request, "webhook_signal", None)
        sources = [
            order_params if isinstance(order_params, dict) else {},
            webhook_signal if isinstance(webhook_signal, dict) else {},
        ]
        for source in sources:
            if source.get("force_broker_squareoff") is True:
                return True
            order_action = str(source.get("order_action") or "").strip().lower()
            if order_action in {"force_kill_switch_exit", "forced_squareoff"}:
                return True
            source_name = str(source.get("source") or "").strip().lower()
            if source_name == "superadmin_force_kill_switch":
                return True
        return False

    def release_reservation(self, reservation_key: Optional[str]) -> None:
        if reservation_key:
            cache.delete(reservation_key)

    def release_trade_limit_reservation(self, reservation_key: Optional[str]) -> None:
        release_successful_buy_slot(reservation_key)

    def complete_trade_limit_reservation(self, reservation_key: Optional[str]) -> None:
        complete_successful_buy_slot(reservation_key)

    @staticmethod
    def _duplicate_key(
        client_id: int,
        symbol: str,
        strike: Optional[float],
        option_type: str,
        transaction_type: str,
    ) -> str:
        base = "|".join(
            [
                str(client_id),
                symbol,
                str(strike or ""),
                option_type,
                transaction_type,
            ]
        )
        digest = hashlib.sha256(base.encode()).hexdigest()[:24]
        return f"risk:dup:{digest}"


_risk_manager: Optional[RiskManager] = None


def get_risk_manager() -> RiskManager:
    global _risk_manager
    if _risk_manager is None:
        _risk_manager = RiskManager()
    return _risk_manager
