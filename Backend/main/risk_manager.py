"""
Centralized execution risk controls for webhook-driven trading.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional, Dict, Any

from django.core.cache import cache
from django.utils import timezone

from main.models import TradingLog
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

        daily_limit = int(
            (getattr(getattr(request, "trade", None), "trade_limit", 0) or DEFAULT_MAX_DAILY_TRADES_PER_CLIENT) * 2
        )
        daily_trade_count = TradingLog.objects.filter(
            client=request.user,
            date=timezone.localdate(),
            symbol=symbol,
        ).count()
        if daily_trade_count >= daily_limit:
            return RiskCheckResult(
                False,
                "Daily trade limit reached for this client and symbol.",
                "DAILY_TRADE_LIMIT_REACHED",
            )

        minute_key = f"risk:minute:{client_id}:{timezone.now().strftime('%Y%m%d%H%M')}"
        cache.add(minute_key, 0, timeout=60)
        try:
            minute_count = cache.incr(minute_key)
        except Exception:
            minute_count = int(cache.get(minute_key, 0) or 0) + 1
            cache.set(minute_key, minute_count, timeout=60)

        if minute_count > MAX_ORDERS_PER_MINUTE_PER_CLIENT:
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
        return RiskCheckResult(True, reservation_key=duplicate_key)

    def release_reservation(self, reservation_key: Optional[str]) -> None:
        if reservation_key:
            cache.delete(reservation_key)

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
