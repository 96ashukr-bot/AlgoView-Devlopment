"""Fallback option-premium lookup used when broker quote entitlements are missing."""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional

import requests
from django.core.cache import cache

from main.broker_order_utils import extract_ltp_from_quote_payload, to_float

logger = logging.getLogger("main")

NSE_BASE_URL = "https://www.nseindia.com"
NSE_OPTION_CHAIN_URL = "https://www.nseindia.com/api/option-chain-indices"
NSE_SUPPORTED_INDEX_OPTIONS = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "NIFTYNXT50"}
NSE_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "application/json,text/plain,*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": "https://www.nseindia.com/option-chain",
}


@dataclass(frozen=True)
class OptionContractHint:
    underlying: str
    strike: float
    option_type: str
    expiry: Optional[datetime] = None


def _normalize_underlying(value: Any) -> str:
    return re.sub(r"[^A-Z0-9]", "", str(value or "").upper())


def _parse_month(month: str) -> Optional[int]:
    try:
        return datetime.strptime(month[:3].title(), "%b").month
    except ValueError:
        return None


def _parse_expiry_date(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    expiry_text = str(value or "").strip()
    if not expiry_text:
        return None
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d%b%Y", "%d%b%y", "%d%m%Y"):
        try:
            return datetime.strptime(expiry_text, fmt)
        except ValueError:
            continue
    return None


def _parse_option_contract(symbol: Any, expiry_date: Any = None, underlying: Any = None) -> Optional[OptionContractHint]:
    raw_symbol = str(symbol or "").strip().upper()
    normalized_symbol = raw_symbol.replace(" ", "").upper()
    parsed_expiry = _parse_expiry_date(expiry_date)

    # Upstox display style: NIFTY 23400 PE 19 MAY 26
    spaced_match = re.match(
        r"^(?P<under>[A-Z0-9]+)\s+(?P<strike>\d+(?:\.\d+)?)\s+(?P<opt>CE|PE)\s+"
        r"(?P<day>\d{1,2})\s+(?P<mon>[A-Z]{3})\s+(?P<yy>\d{2,4})$",
        raw_symbol,
    )
    if spaced_match:
        month = _parse_month(spaced_match.group("mon"))
        year_text = spaced_match.group("yy")
        year = int(year_text) if len(year_text) == 4 else 2000 + int(year_text)
        expiry = parsed_expiry
        if month:
            expiry = expiry or datetime(year, month, int(spaced_match.group("day")))
        return OptionContractHint(
            underlying=_normalize_underlying(underlying or spaced_match.group("under")),
            strike=float(spaced_match.group("strike")),
            option_type=spaced_match.group("opt"),
            expiry=expiry,
        )

    # Dhan style: NIFTY-May2026-23500-PE
    dhan_match = re.match(
        r"^(?P<under>[A-Z0-9]+)-(?P<mon>[A-Z]{3,9})(?P<year>20\d{2})-(?P<strike>\d+(?:\.\d+)?)-(?P<opt>CE|PE)$",
        normalized_symbol,
    )
    if dhan_match:
        month = _parse_month(dhan_match.group("mon"))
        expiry = parsed_expiry
        if month:
            expiry = expiry or datetime(int(dhan_match.group("year")), month, 1)
        return OptionContractHint(
            underlying=_normalize_underlying(underlying or dhan_match.group("under")),
            strike=float(dhan_match.group("strike")),
            option_type=dhan_match.group("opt"),
            expiry=expiry,
        )

    # Dhan normalized style after symbol cleanup: NIFTYMAY202623500PE
    dhan_compact_match = re.match(
        r"^(?P<under>[A-Z0-9]+?)(?P<mon>JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)"
        r"(?P<year>20\d{2})(?P<strike>\d+(?:\.\d+)?)(?P<opt>CE|PE)$",
        normalized_symbol,
    )
    if dhan_compact_match:
        month = _parse_month(dhan_compact_match.group("mon"))
        expiry = parsed_expiry
        if month:
            expiry = expiry or datetime(int(dhan_compact_match.group("year")), month, 1)
        return OptionContractHint(
            underlying=_normalize_underlying(underlying or dhan_compact_match.group("under")),
            strike=float(dhan_compact_match.group("strike")),
            option_type=dhan_compact_match.group("opt"),
            expiry=expiry,
        )

    # Upstox compact style: NIFTY2651923400PE = YY M DD STRIKE PE
    upstox_compact_match = re.match(
        r"^(?P<under>[A-Z0-9]+?)(?P<yy>\d{2})(?P<mon>[1-9OND])(?P<day>\d{2})"
        r"(?P<strike>\d+(?:\.\d+)?)(?P<opt>CE|PE)$",
        normalized_symbol,
    )
    if upstox_compact_match:
        month_code = upstox_compact_match.group("mon")
        month = {"O": 10, "N": 11, "D": 12}.get(month_code, int(month_code) if month_code.isdigit() else None)
        year = 2000 + int(upstox_compact_match.group("yy"))
        expiry = parsed_expiry
        if month:
            expiry = expiry or datetime(year, month, int(upstox_compact_match.group("day")))
        return OptionContractHint(
            underlying=_normalize_underlying(underlying or upstox_compact_match.group("under")),
            strike=float(upstox_compact_match.group("strike")),
            option_type=upstox_compact_match.group("opt"),
            expiry=expiry,
        )

    # Kite monthly style seen in production: NIFTY26MAY23500PE = YY MON STRIKE PE.
    # It does not carry an expiry day, so we match nearest option-chain row by strike.
    kite_monthly_match = re.match(
        r"^(?P<under>[A-Z0-9]+?)(?P<yy>\d{2})(?P<mon>[A-Z]{3})(?P<strike>\d+(?:\.\d+)?)(?P<opt>CE|PE)$",
        normalized_symbol,
    )
    if kite_monthly_match:
        return OptionContractHint(
            underlying=_normalize_underlying(underlying or kite_monthly_match.group("under")),
            strike=float(kite_monthly_match.group("strike")),
            option_type=kite_monthly_match.group("opt"),
            expiry=parsed_expiry,
        )

    if parsed_expiry:
        generic_match = re.match(r"^(?P<under>[A-Z0-9]+).*?(?P<strike>\d+(?:\.\d+)?)(?P<opt>CE|PE)$", normalized_symbol)
        if generic_match:
            return OptionContractHint(
                underlying=_normalize_underlying(underlying or generic_match.group("under")),
                strike=float(generic_match.group("strike")),
                option_type=generic_match.group("opt"),
                expiry=parsed_expiry,
            )

    return None


def _nse_expiry_text(expiry: Optional[datetime]) -> Optional[str]:
    if not expiry:
        return None
    return expiry.strftime("%d-%b-%Y")


def _extract_option_chain_ltp(payload: Any, contract: OptionContractHint) -> Optional[float]:
    if not isinstance(payload, dict):
        return None
    records = payload.get("records") or {}
    rows = records.get("data") or []
    expected_expiry = _nse_expiry_text(contract.expiry)

    for row in rows:
        if not isinstance(row, dict):
            continue
        strike = to_float(row.get("strikePrice"))
        if strike is None or abs(strike - contract.strike) > 0.001:
            continue
        if expected_expiry and str(row.get("expiryDate") or "").strip().lower() != expected_expiry.lower():
            continue
        option_node = row.get(contract.option_type)
        ltp = extract_ltp_from_quote_payload(option_node)
        if ltp and ltp > 0:
            return float(ltp)
    return None


def _cache_keys_for_contract(contract: OptionContractHint) -> list[str]:
    expiry_key = contract.expiry.strftime("%Y%m%d") if contract.expiry else "any"
    base = f"{contract.underlying}:{contract.strike:g}:{contract.option_type}"
    keys = [f"option-ltp:{base}:{expiry_key}", f"option-ltp:{base}:any"]
    return list(dict.fromkeys(keys))


def cache_option_ltp(
    symbol: Any,
    ltp: Any,
    *,
    expiry_date: Any = None,
    underlying: Any = None,
    source: str = "",
    timeout: int = 180,
) -> Optional[float]:
    price = to_float(ltp)
    if not price or price <= 0:
        return None
    contract = _parse_option_contract(symbol, expiry_date=expiry_date, underlying=underlying)
    if not contract:
        return None
    payload = {
        "ltp": float(price),
        "source": source,
        "symbol": str(symbol or ""),
        "cached_at": datetime.utcnow().isoformat(),
    }
    for key in _cache_keys_for_contract(contract):
        cache.set(key, payload, timeout=timeout)
    return float(price)


def get_cached_option_ltp(symbol: Any, *, expiry_date: Any = None, underlying: Any = None) -> Optional[float]:
    contract = _parse_option_contract(symbol, expiry_date=expiry_date, underlying=underlying)
    if not contract:
        return None
    for key in _cache_keys_for_contract(contract):
        payload = cache.get(key)
        if isinstance(payload, dict):
            price = to_float(payload.get("ltp"))
            if price and price > 0:
                logger.info(
                    "Using cached option premium for %s %s%s expiry %s from %s.",
                    contract.underlying,
                    f"{contract.strike:g}",
                    contract.option_type,
                    _nse_expiry_text(contract.expiry) or "any",
                    payload.get("source") or "unknown",
                )
                return float(price)
    return None


def fetch_nse_option_chain_ltp(
    symbol: Any,
    *,
    expiry_date: Any = None,
    underlying: Any = None,
    proxy_config: Optional[dict[str, str]] = None,
    user: Any = None,
    timeout: int = 6,
) -> Optional[float]:
    """Fetch index-option premium from NSE option chain through the assigned proxy."""
    contract = _parse_option_contract(symbol, expiry_date=expiry_date, underlying=underlying)
    if not contract:
        logger.warning(f"[{user}] NSE option-chain fallback could not parse option contract from {symbol}.")
        return None
    if contract.underlying not in NSE_SUPPORTED_INDEX_OPTIONS:
        logger.warning(f"[{user}] NSE option-chain fallback unsupported underlying {contract.underlying} for {symbol}.")
        return None

    try:
        with requests.Session() as session:
            session.headers.update(NSE_HEADERS)
            if proxy_config:
                session.proxies.update(proxy_config)
            session.get(NSE_BASE_URL, timeout=timeout)
            response = session.get(
                NSE_OPTION_CHAIN_URL,
                params={"symbol": contract.underlying},
                timeout=timeout,
            )
            payload = response.json() if response.content else {}
            if response.status_code != 200:
                logger.warning(
                    f"[{user}] NSE option-chain fallback failed for {symbol}: "
                    f"{response.status_code} {str(payload)[:300]}"
                )
                return get_cached_option_ltp(symbol, expiry_date=contract.expiry, underlying=contract.underlying)
            ltp = _extract_option_chain_ltp(payload, contract)
            if ltp is None:
                logger.warning(
                    f"[{user}] NSE option-chain fallback did not find premium for "
                    f"{contract.underlying} {contract.strike:g}{contract.option_type} "
                    f"expiry {_nse_expiry_text(contract.expiry) or 'any'}."
                )
            if ltp is not None:
                cache_option_ltp(symbol, ltp, expiry_date=contract.expiry, underlying=contract.underlying, source="nse-option-chain")
                return ltp
            return get_cached_option_ltp(symbol, expiry_date=contract.expiry, underlying=contract.underlying)
    except Exception as exc:
        logger.warning(f"[{user}] NSE option-chain fallback failed for {symbol}: {str(exc)}")
        return get_cached_option_ltp(symbol, expiry_date=contract.expiry, underlying=contract.underlying)
