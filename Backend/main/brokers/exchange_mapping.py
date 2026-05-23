from __future__ import annotations

from typing import Any

from main.broker_registry import normalize_broker_name


BSE_INDEX_DERIVATIVE_UNDERLYINGS = {"SENSEX", "BANKEX", "SENSEX50"}
BSE_DERIVATIVE_EXCHANGES = {"BFO", "BSE_FO", "BSE_FNO", "BSE_DERIVATIVE", "BSE_DERIVATIVES"}


def _normalized_text(value: Any) -> str:
    return str(value or "").strip().upper().replace(" ", "")


def is_bse_index_derivative(*, underlying: Any = None, exchange: Any = None) -> bool:
    normalized_underlying = _normalized_text(underlying)
    normalized_exchange = _normalized_text(exchange)
    return (
        normalized_underlying in BSE_INDEX_DERIVATIVE_UNDERLYINGS
        or normalized_exchange in BSE_DERIVATIVE_EXCHANGES
    )


def normalize_broker_exchange(broker_name: Any, exchange: Any = None, underlying: Any = None) -> str:
    normalized_exchange = _normalized_text(exchange) or "NFO"
    if normalized_exchange == "BSE" and not is_bse_index_derivative(underlying=underlying, exchange=exchange):
        return "BSE"
    if not is_bse_index_derivative(underlying=underlying, exchange=exchange):
        return normalized_exchange

    normalized_broker = normalize_broker_name(str(broker_name or ""))
    return {
        "angel one": "BFO",
        "angelone": "BFO",
        "alice blue": "BFO",
        "aliceblue": "BFO",
        "zerodha": "BFO",
        "dhan": "BSE_FNO",
        "fyers": "BSE_FO",
        "upstox": "BSE",
        "5paisa": "BSE",
        "five paisa": "BSE",
    }.get(normalized_broker, "BFO")


def normalize_fivepaisa_exchange(exchange: Any = None, underlying: Any = None) -> tuple[str, str]:
    if is_bse_index_derivative(underlying=underlying, exchange=exchange):
        return "bse_fo", "B"
    return "nse_fo", "N"
