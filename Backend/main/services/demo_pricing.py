"""Exact-contract market prices for simulated option fills."""
import logging
import math
from datetime import datetime

from django.utils import timezone

from main.services.live_price_cache import get_live_price

logger = logging.getLogger(__name__)


def _premium(value):
    try:
        price = float(value)
    except (TypeError, ValueError, OverflowError):
        return None
    return price if math.isfinite(price) and price > 0 else None


def get_demo_option_premium(*, underlying, expiry_date, strike, option_type):
    """Never infer a premium from the strike, limit, or previous entry price."""
    if isinstance(expiry_date, datetime):
        if timezone.is_aware(expiry_date):
            expiry_date = timezone.localtime(expiry_date)
        expiry_date = expiry_date.date()
    expiry = str(expiry_date or "")
    option_type = str(option_type or "").upper()
    if not underlying or not expiry or _premium(strike) is None or option_type not in {"CE", "PE"}:
        return None
    contract = dict(underlying=underlying, expiry_date=expiry, strike=strike, option_type=option_type)
    try:
        payload = get_live_price(**contract, max_age_seconds=15)
        if isinstance(payload, dict) and payload.get("is_fresh"):
            premium = _premium(payload.get("ltp"))
            if premium is not None:
                return premium

        # A newly selected contract may not yet be subscribed by the collector.
        # Resolve all four contract fields, then request its market-data quote.
        from main.services.upstox_market_data import (
            fetch_central_upstox_option_ltp,
            get_upstox_instrument_resolver,
        )
        instrument = get_upstox_instrument_resolver().resolve_contract(**contract)
        if instrument is not None:
            return _premium(fetch_central_upstox_option_ltp(instrument))
    except Exception:
        logger.warning("Demo option premium unavailable for %s %s %s %s", underlying, expiry, strike, option_type)
    return None
