"""Stable queue routing and telemetry helpers for risk-reducing exits."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from django.utils import timezone


EXIT_DISPATCH_QUEUE = "priority_exit_dispatch"
EXIT_QUEUE_PREFIX = "exit_"
DEFAULT_EXIT_QUEUE = "priority_order_exits"

_BROKER_QUEUE_NAMES = {
    "angel one": "angelone",
    "angelone": "angelone",
    "angle one": "angelone",
    "zerodha": "zerodha",
    "kite": "zerodha",
    "upstox": "upstox",
    "groww": "groww",
    "grow": "groww",
    "dhan": "dhan",
    "alice blue": "aliceblue",
    "aliceblue": "aliceblue",
    "fyers": "fyers",
    "5paisa": "5paisa",
    "five paisa": "5paisa",
    "fivepaisa": "5paisa",
}


def normalize_exit_broker(broker: Any) -> str:
    return " ".join(str(broker or "").strip().casefold().replace("_", " ").split())


def exit_queue_for_broker(broker: Any) -> str:
    suffix = _BROKER_QUEUE_NAMES.get(normalize_exit_broker(broker))
    return f"{EXIT_QUEUE_PREFIX}{suffix}" if suffix else DEFAULT_EXIT_QUEUE


def exit_queue_names() -> tuple[str, ...]:
    return (EXIT_DISPATCH_QUEUE, DEFAULT_EXIT_QUEUE) + tuple(
        f"{EXIT_QUEUE_PREFIX}{suffix}" for suffix in sorted(set(_BROKER_QUEUE_NAMES.values()))
    )


def exit_timing(payload: dict | None) -> dict:
    """Return the mutable, nested timing map used across every exit stage."""
    if not isinstance(payload, dict):
        return {}
    params = payload.get("order_params") if isinstance(payload.get("order_params"), dict) else payload
    timing = params.get("exit_timing")
    if not isinstance(timing, dict):
        timing = {}
        params["exit_timing"] = timing
    return timing


def stamp_exit(payload: dict | None, stage: str, value: Any = None) -> str:
    stamp = str(value or timezone.now().isoformat())
    timing = exit_timing(payload)
    if timing is not None:
        timing[stage] = stamp
    return stamp


def elapsed_ms(start: Any, end: Any = None) -> int | None:
    try:
        start_dt = datetime.fromisoformat(str(start).replace("Z", "+00:00"))
        end_dt = datetime.fromisoformat(str(end or timezone.now().isoformat()).replace("Z", "+00:00"))
        return max(0, round((end_dt - start_dt).total_seconds() * 1000))
    except (TypeError, ValueError):
        return None
