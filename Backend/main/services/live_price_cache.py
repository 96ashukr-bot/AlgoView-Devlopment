from __future__ import annotations

import re
from datetime import datetime, timezone as dt_timezone
from typing import Any, Iterable, Optional

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


LIVE_PRICE_PREFIX = "live-price"
LIVE_PRICE_TIMEOUT_SECONDS = getattr(settings, "LIVE_PRICE_CACHE_TIMEOUT_SECONDS", 60)
LIVE_PRICE_FRESH_SECONDS = getattr(settings, "LIVE_PRICE_FRESH_SECONDS", 5)


def normalize_symbol_key(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _now_iso() -> str:
    return timezone.now().isoformat()


def _parse_iso(value: Any) -> Optional[datetime]:
    if not value:
        return None
    try:
        parsed = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except (TypeError, ValueError):
        return None
    if timezone.is_naive(parsed):
        parsed = parsed.replace(tzinfo=dt_timezone.utc)
    return parsed


def _price_key(instrument_key: str) -> str:
    return f"{LIVE_PRICE_PREFIX}:instrument:{instrument_key}"


def _alias_key(alias: str) -> Optional[str]:
    normalized = normalize_symbol_key(alias)
    if not normalized:
        return None
    return f"{LIVE_PRICE_PREFIX}:alias:{normalized}"


def _contract_key(underlying: Any, expiry_date: Any, strike: Any, option_type: Any) -> Optional[str]:
    underlying_key = normalize_symbol_key(underlying)
    option_key = normalize_symbol_key(option_type)
    if not (underlying_key and option_key and strike not in (None, "")):
        return None
    try:
        strike_key = f"{float(strike):g}"
    except (TypeError, ValueError):
        return None

    expiry_key = None
    if isinstance(expiry_date, datetime):
        expiry_key = expiry_date.strftime("%Y%m%d")
    elif expiry_date:
        expiry_text = str(expiry_date).strip()
        for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d%b%Y", "%d%b%y"):
            try:
                expiry_key = datetime.strptime(expiry_text, fmt).strftime("%Y%m%d")
                break
            except ValueError:
                continue
    if not expiry_key:
        return None
    return f"{LIVE_PRICE_PREFIX}:contract:{underlying_key}:{expiry_key}:{strike_key}:{option_key}"


def build_live_price_payload(
    *,
    instrument_key: str,
    ltp: Any,
    source: str,
    trading_symbol: Any = None,
    exchange_ts: Any = None,
    underlying: Any = None,
    expiry_date: Any = None,
    strike: Any = None,
    option_type: Any = None,
) -> Optional[dict[str, Any]]:
    try:
        price = float(ltp)
    except (TypeError, ValueError):
        return None
    if price <= 0 or not instrument_key:
        return None

    received_at = _now_iso()
    return {
        "instrument_key": str(instrument_key),
        "trading_symbol": str(trading_symbol or ""),
        "ltp": price,
        "source": source,
        "exchange_ts": str(exchange_ts or ""),
        "received_at": received_at,
        "underlying": str(underlying or ""),
        "expiry_date": expiry_date.isoformat() if isinstance(expiry_date, datetime) else str(expiry_date or ""),
        "strike": float(strike) if strike not in (None, "") else None,
        "option_type": str(option_type or ""),
    }


def cache_live_price(payload: dict[str, Any], aliases: Iterable[Any] = ()) -> None:
    instrument_key = payload.get("instrument_key")
    if not instrument_key:
        return
    cache.set(_price_key(instrument_key), payload, timeout=LIVE_PRICE_TIMEOUT_SECONDS)

    alias_keys = []
    for alias in aliases:
        key = _alias_key(alias)
        if key:
            alias_keys.append(key)

    contract_key = _contract_key(
        payload.get("underlying"),
        payload.get("expiry_date"),
        payload.get("strike"),
        payload.get("option_type"),
    )
    if contract_key:
        alias_keys.append(contract_key)

    for alias_key in dict.fromkeys(alias_keys):
        cache.set(alias_key, instrument_key, timeout=LIVE_PRICE_TIMEOUT_SECONDS)


def get_live_price(
    *,
    instrument_key: Any = None,
    trading_symbol: Any = None,
    underlying: Any = None,
    expiry_date: Any = None,
    strike: Any = None,
    option_type: Any = None,
    max_age_seconds: Optional[int] = None,
) -> Optional[dict[str, Any]]:
    resolved_instrument_key = str(instrument_key or "").strip()
    if not resolved_instrument_key and trading_symbol:
        alias = cache.get(_alias_key(trading_symbol) or "")
        resolved_instrument_key = str(alias or "").strip()

    if not resolved_instrument_key:
        contract_alias = _contract_key(underlying, expiry_date, strike, option_type)
        if contract_alias:
            resolved_instrument_key = str(cache.get(contract_alias) or "").strip()

    if not resolved_instrument_key:
        return None

    payload = cache.get(_price_key(resolved_instrument_key))
    if not isinstance(payload, dict):
        return None

    received_at = _parse_iso(payload.get("received_at"))
    if not received_at:
        payload = {**payload, "is_fresh": False, "age_seconds": None}
        return payload

    age_seconds = max((timezone.now() - received_at).total_seconds(), 0)
    freshness_limit = LIVE_PRICE_FRESH_SECONDS if max_age_seconds is None else max_age_seconds
    return {
        **payload,
        "age_seconds": round(age_seconds, 3),
        "is_fresh": age_seconds <= freshness_limit,
    }

