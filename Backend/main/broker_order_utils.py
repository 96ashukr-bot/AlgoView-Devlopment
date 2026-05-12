"""Shared broker order helpers used outside the Angel One adapter."""

from __future__ import annotations

import re
from typing import Any, Optional

from main.angelone.constants import (
    DEFAULT_BUFFER_PERCENTAGE,
    DEFAULT_TICK_SIZE,
    MAX_VALID_LTP,
    MIN_VALID_LTP,
)


def to_float(value: Any) -> Optional[float]:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def normalize_order_type(order_type: Any) -> str:
    normalized = str(order_type or "LIMIT").strip().upper()
    if normalized in {"SLM", "SL-MARKET"}:
        return "SL-M"
    return normalized


def is_valid_market_price(value: Any) -> bool:
    price = to_float(value)
    return price is not None and MIN_VALID_LTP <= price <= MAX_VALID_LTP


def round_to_tick(price: float, tick_size: float = DEFAULT_TICK_SIZE) -> float:
    if tick_size <= 0:
        return round(price, 2)
    ticks = round(price / tick_size)
    return round(ticks * tick_size, 2)


def calculate_buffered_limit_price(
    ltp: Any,
    side: str,
    buffer_percentage: Any = DEFAULT_BUFFER_PERCENTAGE,
    tick_size: float = DEFAULT_TICK_SIZE,
) -> Optional[float]:
    live_price = to_float(ltp)
    if live_price is None or live_price <= 0:
        return None

    buffer_percent = to_float(buffer_percentage)
    if buffer_percent is None:
        buffer_percent = float(DEFAULT_BUFFER_PERCENTAGE)

    multiplier = 1 + (buffer_percent / 100.0) if str(side).upper() == "BUY" else 1 - (buffer_percent / 100.0)
    return round_to_tick(live_price * multiplier, tick_size=tick_size)


def resolve_limit_price(explicit_price: Any, ltp: Any, side: str, buffer_percentage: Any = DEFAULT_BUFFER_PERCENTAGE) -> Optional[float]:
    requested_price = to_float(explicit_price)
    if requested_price and requested_price > 0:
        return round_to_tick(requested_price)
    return calculate_buffered_limit_price(ltp, side, buffer_percentage=buffer_percentage)


def is_option_symbol(symbol: Any) -> bool:
    normalized = str(symbol or "").replace(" ", "").replace("-", "").upper()
    return bool(re.search(r"\d+(?:\.\d+)?(CE|PE)$", normalized) or re.search(r"(CALL|PUT)$", normalized))


def resolve_limit_reference_price(symbol: Any, ltp: Any, live_price: Any, entry_price: Any = None, exit_price: Any = None) -> Optional[float]:
    live_ltp = to_float(ltp)
    if live_ltp and live_ltp > 0:
        return live_ltp

    # For option contracts, LivePrice/entry/exit values can be the underlying index price
    # from the signal, which would create circuit-breaking option limit prices.
    if is_option_symbol(symbol):
        return None

    for candidate in (live_price, entry_price, exit_price):
        value = to_float(candidate)
        if value and value > 0:
            return value
    return None
