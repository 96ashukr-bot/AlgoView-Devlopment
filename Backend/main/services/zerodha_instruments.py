"""Resolve Zerodha options from exact exchange-listed contract attributes."""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from main.broker_instrument_cache import load_zerodha_instrument_index


def _expiry_date(value):
    if isinstance(value, datetime):
        parsed = value
    elif isinstance(value, date):
        return value
    else:
        parsed = datetime.fromisoformat(str(value).strip().replace("Z", "+00:00"))
    if parsed.tzinfo is not None:
        parsed = parsed.astimezone(ZoneInfo("Asia/Kolkata"))
    return parsed.date()


def resolve_zerodha_option_contract(order, exchange="NFO"):
    exchange = str(exchange).strip().upper()
    if exchange not in {"NFO", "BFO"}:
        raise ValueError("Unsupported Zerodha option exchange.")
    nested = order.get("order_params") if isinstance(order.get("order_params"), dict) else {}
    underlying = str(order.get("symbol") or order.get("underlying") or order.get("Index_Symbol") or "").strip().upper()
    side = str(order.get("option_type") or order.get("Type") or "").strip().upper()
    try:
        strike = Decimal(str(order.get("strike") or order.get("strike_price") or ""))
        if not strike.is_finite() or strike <= 0 or side not in {"CE", "PE"} or not underlying:
            raise ValueError
        dates = {
            _expiry_date(source[key])
            for source in (order, nested)
            for key in ("expiry", "expiry_date")
            if source.get(key) not in (None, "")
        }
        day, month = order.get("day"), order.get("month")
        year = order.get("fullyear") or order.get("full_year") or order.get("year")
        if day and month and year:
            year = str(year)
            year_format = "%Y" if len(year) == 4 else "%y"
            dates.add(datetime.strptime(f"{int(day):02d}{str(month)[:3]}{year}", "%d%b" + year_format).date())
        if len(dates) != 1:
            raise ValueError
        expiry = dates.pop()
    except (ValueError, TypeError, InvalidOperation, OverflowError):
        raise ValueError(f"Zerodha {exchange} order requires one consistent expiry, underlying, strike and option type.") from None

    matches = {}
    for row in load_zerodha_instrument_index(exchange).values():
        if str(row.get("exchange") or "").upper() != exchange or str(row.get("name") or "").upper() != underlying:
            continue
        if str(row.get("instrument_type") or "").upper() != side:
            continue
        try:
            if Decimal(str(row.get("strike"))) != strike or _expiry_date(row.get("expiry")) != expiry:
                continue
            token = int(row.get("instrument_token") or 0)
        except (ValueError, TypeError, InvalidOperation, OverflowError):
            continue
        ticker = str(row.get("tradingsymbol") or "").strip()
        if token <= 0 or not ticker:
            raise ValueError(f"Zerodha {exchange} master contains an invalid instrument identifier.")
        matches[(ticker, token)] = row
    if len(matches) != 1:
        reason = "not found" if not matches else "ambiguous"
        raise ValueError(
            f"Exact Zerodha {exchange} contract {underlying} {expiry.isoformat()} {strike} {side} is {reason}; order was not submitted."
        )
    return dict(next(iter(matches.values())), expiry=expiry.isoformat())


def resolve_zerodha_bfo_contract(order):
    return resolve_zerodha_option_contract(order, exchange="BFO")
