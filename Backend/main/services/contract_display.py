from __future__ import annotations

from datetime import datetime
from typing import Any, Optional


INDEX_UNDERLYINGS = {"NIFTY", "BANKNIFTY", "FINNIFTY", "MIDCPNIFTY", "SENSEX", "BANKEX"}


def _to_float(value: Any) -> Optional[float]:
    if value in (None, "", "None"):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _parse_expiry(value: Any) -> Optional[datetime]:
    if isinstance(value, datetime):
        return value
    text = str(value or "").strip()
    if not text:
        return None
    for fmt in ("%Y-%m-%d", "%d-%b-%Y", "%d%b%Y", "%d%b%y", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def _expiry_from_parts(day: Any, month: Any, year: Any) -> Optional[datetime]:
    if not (day and month and year):
        return None
    year_text = str(year).strip()
    if len(year_text) == 2:
        year_text = f"20{year_text}"
    try:
        return datetime.strptime(f"{int(float(day)):02d}{str(month)[:3].upper()}{year_text}", "%d%b%Y")
    except (TypeError, ValueError):
        return None


def looks_like_full_option_symbol(value: Any) -> bool:
    text = str(value or "").strip().upper()
    return len(text) > 6 and ("CE" in text or "PE" in text)


def build_option_display_symbol(*, current_symbol: Any = None, index_symbol: Any = None, order_params: Any = None, metadata: Any = None) -> str:
    for candidate in (index_symbol, current_symbol):
        if looks_like_full_option_symbol(candidate):
            return str(candidate).strip()

    params = order_params if isinstance(order_params, dict) else {}
    meta = metadata if isinstance(metadata, dict) else {}

    underlying = str(meta.get("underlying") or params.get("symbol") or params.get("underlying") or current_symbol or index_symbol or "").strip().upper()
    strike = _to_float(meta.get("strike") or params.get("strike") or params.get("strike_price") or params.get("default_price"))
    option_type = str(meta.get("option_type") or params.get("option_type") or params.get("Type") or "").strip().upper()
    expiry = _parse_expiry(meta.get("expiry") or params.get("expiry") or params.get("expiry_date")) or _expiry_from_parts(
        params.get("day"),
        params.get("month"),
        params.get("fullyear") or params.get("year"),
    )

    if not (underlying and strike is not None and option_type in {"CE", "PE"} and expiry):
        return str(index_symbol or current_symbol or "").strip()

    strike_text = f"{strike:g}"
    return f"{underlying}{expiry.strftime('%d%b%y').upper()}{strike_text}{option_type}"
