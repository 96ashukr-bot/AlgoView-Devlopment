from __future__ import annotations

from main.broker_registry import normalize_broker_name
from main.brokers.aliceblue import AliceBlueBroker
from main.brokers.angelone import AngelOneBroker
from main.brokers.dhan import DhanBroker
from main.brokers.fivepaisa import FivePaisaBroker
from main.brokers.fyers import FyersBroker
from main.brokers.upstox import UpstoxBroker
from main.brokers.zerodha import ZerodhaBroker

BROKER_ADAPTERS = {
    "angel one": AngelOneBroker,
    "angelone": AngelOneBroker,
    "alice blue": AliceBlueBroker,
    "aliceblue": AliceBlueBroker,
    "upstox": UpstoxBroker,
    "zerodha": ZerodhaBroker,
    "5paisa": FivePaisaBroker,
    "five paisa": FivePaisaBroker,
    "fyers": FyersBroker,
    "dhan": DhanBroker,
}


def get_broker_adapter(broker_name_or_details, broker_details=None):
    if broker_details is None:
        broker_details = broker_name_or_details
        broker_name = getattr(getattr(broker_details, "broker_name", None), "broker_name", "")
    else:
        broker_name = broker_name_or_details
    normalized_name = normalize_broker_name(broker_name)
    adapter_class = BROKER_ADAPTERS.get(normalized_name)
    if not adapter_class:
        raise ValueError(f"Unsupported execution broker: {normalized_name or 'unknown'}")
    return adapter_class(broker_details)
