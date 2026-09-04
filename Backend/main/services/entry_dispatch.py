"""Stable broker-isolated Celery queue routing for BUY entries."""

from __future__ import annotations

from typing import Any


DEFAULT_ENTRY_QUEUE = "priority_entry"
_BROKER_QUEUES = {
    "angel one": "entry_angelone",
    "angelone": "entry_angelone",
    "zerodha": "entry_zerodha",
    "upstox": "entry_upstox",
    "groww": "entry_groww",
    "dhan": "entry_dhan",
    "alice blue": "entry_aliceblue",
    "aliceblue": "entry_aliceblue",
    "fyers": "entry_fyers",
    "5paisa": "entry_5paisa",
    "5 paisa": "entry_5paisa",
    "demo": "entry_demo",
    "demo broker": "entry_demo",
}


def entry_queue_for_broker(broker: Any) -> str:
    normalized = " ".join(str(broker or "").strip().casefold().replace("_", " ").split())
    return _BROKER_QUEUES.get(normalized, DEFAULT_ENTRY_QUEUE)


def entry_queue_names() -> tuple[str, ...]:
    return (DEFAULT_ENTRY_QUEUE,) + tuple(sorted(set(_BROKER_QUEUES.values())))
