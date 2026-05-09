from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from main.services.broker_transport import BrokerTransport, ProxyRoutingRequiredError


class BaseBrokerAdapter(ABC):
    broker_name = "base"
    supports_proxy = False

    def __init__(self, broker_details):
        self.broker_details = broker_details

    def require_proxy_config(self, proxy_config: dict[str, str] | None) -> dict[str, str]:
        if not proxy_config:
            raise ProxyRoutingRequiredError(
                f"{self.broker_name} broker communication requires an assigned proxy/static-IP route."
            )
        return proxy_config

    def get_transport(self, proxy_config: dict[str, str] | None = None) -> BrokerTransport:
        return BrokerTransport(broker_details=self.broker_details, proxy_config=self.require_proxy_config(proxy_config))

    def login(self, proxy_config: dict[str, str] | None = None) -> dict[str, Any]:
        return {"status": "not_required"}

    @abstractmethod
    def place_order(self, payload: dict[str, Any], proxy_config: dict[str, str] | None = None) -> dict[str, Any]:
        raise NotImplementedError

    def modify_order(self, payload: dict[str, Any], proxy_config: dict[str, str] | None = None) -> dict[str, Any]:
        return {"status": "not_implemented"}

    def cancel_order(self, payload: dict[str, Any], proxy_config: dict[str, str] | None = None) -> dict[str, Any]:
        return {"status": "not_implemented"}

    def get_orderbook(self, proxy_config: dict[str, str] | None = None) -> dict[str, Any]:
        return {"status": "not_implemented"}

    def get_positions(self, proxy_config: dict[str, str] | None = None) -> dict[str, Any]:
        return {"status": "not_implemented"}

    def get_holdings(self, proxy_config: dict[str, str] | None = None) -> dict[str, Any]:
        return {"status": "not_implemented"}

    def validate_credentials(self, proxy_config: dict[str, str] | None = None) -> dict[str, Any]:
        return {"status": "success"}


BaseBroker = BaseBrokerAdapter


def get_broker_adapter(*args):
    from main.brokers.registry import get_broker_adapter as registry_get_broker_adapter

    return registry_get_broker_adapter(*args)
