from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from main.broker_registry import normalize_broker_name


class BaseBroker(ABC):
    broker_name = "base"

    def __init__(self, broker_details):
        self.broker_details = broker_details

    def login(self) -> dict[str, Any]:
        return {"status": "not_required"}

    @abstractmethod
    def place_order(self, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def get_orderbook(self) -> dict[str, Any]:
        return {"status": "not_implemented"}

    def get_positions(self) -> dict[str, Any]:
        return {"status": "not_implemented"}

    def validate_credentials(self) -> dict[str, Any]:
        return {"status": "success"}


def get_broker_adapter(broker_details):
    broker_name = normalize_broker_name(getattr(getattr(broker_details, "broker_name", None), "broker_name", ""))
    if broker_name == "angel one":
        from main.brokers.angelone import AngelOneBroker

        return AngelOneBroker(broker_details)
    if broker_name == "upstox":
        from main.brokers.upstox import UpstoxBroker

        return UpstoxBroker(broker_details)
    if broker_name == "zerodha":
        from main.brokers.zerodha import ZerodhaBroker

        return ZerodhaBroker(broker_details)
    if broker_name == "alice blue":
        from main.brokers.aliceblue import AliceBlueBroker

        return AliceBlueBroker(broker_details)
    if broker_name == "5paisa":
        from main.brokers.fivepaisa import FivePaisaBroker

        return FivePaisaBroker(broker_details)
    if broker_name == "fyers":
        from main.brokers.fyers import FyersBroker

        return FyersBroker(broker_details)
    if broker_name == "dhan":
        from main.brokers.dhan import DhanBroker

        return DhanBroker(broker_details)
    raise ValueError(f"Unsupported execution-node broker: {broker_name or 'unknown'}")
