from __future__ import annotations

import asyncio
import hashlib
import logging
import ssl
from dataclasses import dataclass
from typing import Any

import requests
import websockets
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from main.models import ClientBrokerdetails, ExecutionNode
from main.services.proxy_utils import build_requests_proxy_config, mask_proxy_url

logger = logging.getLogger("main.broker_transport")


class ProxyRoutingRequiredError(RuntimeError):
    """Raised when broker egress would happen without an assigned execution route."""


def proxy_fingerprint(proxy_config: dict[str, str] | None) -> str:
    if not proxy_config:
        return "missing"
    material = "|".join(f"{key}={value}" for key, value in sorted(proxy_config.items()))
    return hashlib.sha256(material.encode()).hexdigest()[:16]


@dataclass(frozen=True)
class BrokerSessionContext:
    client_id: int
    broker_id: int | None
    execution_node_id: int
    proxy_fingerprint: str

    @classmethod
    def from_broker_details(cls, broker_details: ClientBrokerdetails, proxy_config: dict[str, str]) -> "BrokerSessionContext":
        node = broker_details.execution_node
        if not node:
            raise ProxyRoutingRequiredError("Broker session requires an assigned execution node.")
        return cls(
            client_id=broker_details.client_id,
            broker_id=broker_details.broker_name_id,
            execution_node_id=node.id,
            proxy_fingerprint=proxy_fingerprint(proxy_config),
        )


class ProxyBoundSessionFactory:
    """Creates per-client, per-broker, per-proxy HTTP sessions.

    Sessions are intentionally keyed by execution node and proxy fingerprint to avoid
    reusing pooled sockets across clients or after a proxy credential change.
    """

    _sessions: dict[BrokerSessionContext, requests.Session] = {}
    _lock = asyncio.Lock()

    @classmethod
    async def get_async(cls, context: BrokerSessionContext, proxy_config: dict[str, str]) -> requests.Session:
        async with cls._lock:
            return cls._get_or_create(context, proxy_config)

    @classmethod
    def get(cls, context: BrokerSessionContext, proxy_config: dict[str, str]) -> requests.Session:
        return cls._get_or_create(context, proxy_config)

    @classmethod
    def _get_or_create(cls, context: BrokerSessionContext, proxy_config: dict[str, str]) -> requests.Session:
        if not proxy_config:
            raise ProxyRoutingRequiredError("Proxy config is required for broker HTTP session.")
        session = cls._sessions.get(context)
        if session:
            return session
        session = requests.Session()
        session.proxies.update(proxy_config)
        session.verify = True
        retry = Retry(
            total=2,
            connect=2,
            read=1,
            status=1,
            backoff_factor=0.2,
            status_forcelist=(429, 500, 502, 503, 504),
            allowed_methods=frozenset({"GET", "POST", "PUT", "PATCH", "DELETE"}),
            raise_on_status=False,
        )
        adapter = HTTPAdapter(max_retries=retry, pool_connections=4, pool_maxsize=16)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        cls._sessions[context] = session
        return session

    @classmethod
    def clear_context(cls, context: BrokerSessionContext) -> None:
        session = cls._sessions.pop(context, None)
        if session:
            session.close()


class BrokerTransport:
    """The only broker egress abstraction allowed for proxy-mode execution."""

    def __init__(self, *, broker_details: ClientBrokerdetails, execution_node: ExecutionNode | None = None, proxy_config: dict[str, str] | None = None):
        self.broker_details = broker_details
        self.execution_node = execution_node or broker_details.execution_node
        if not self.execution_node:
            raise ProxyRoutingRequiredError("No execution node assigned to broker details.")
        self.proxy_config = proxy_config or build_requests_proxy_config(self.execution_node)
        if not self.proxy_config:
            raise ProxyRoutingRequiredError("Proxy configuration is required for broker transport.")
        self.context = BrokerSessionContext.from_broker_details(broker_details, self.proxy_config)
        self.session = ProxyBoundSessionFactory.get(self.context, self.proxy_config)

    @property
    def masked_proxy(self) -> str:
        return mask_proxy_url(self.execution_node)

    def request(self, method: str, url: str, **kwargs: Any) -> requests.Response:
        kwargs.setdefault("timeout", 10)
        kwargs["proxies"] = self.proxy_config
        kwargs["verify"] = True
        logger.debug(
            "Broker HTTP request through proxy",
            extra={"client_id": self.context.client_id, "broker_id": self.context.broker_id, "proxy": self.masked_proxy},
        )
        return self.session.request(method.upper(), url, **kwargs)

    async def websocket_connect(self, uri: str, **kwargs: Any):
        ssl_context = kwargs.pop("ssl", None) or ssl.create_default_context()
        kwargs.setdefault("open_timeout", 10)
        kwargs.setdefault("ping_interval", 20)
        kwargs.setdefault("ping_timeout", 20)
        proxy_url = self.proxy_config.get("https") or self.proxy_config.get("http")
        if not proxy_url:
            raise ProxyRoutingRequiredError("WebSocket broker connection requires proxy configuration.")
        logger.debug(
            "Broker websocket through proxy",
            extra={"client_id": self.context.client_id, "broker_id": self.context.broker_id, "proxy": self.masked_proxy},
        )
        return websockets.connect(uri, ssl=ssl_context, proxy=proxy_url, **kwargs)


def build_transport_for_broker(broker_details: ClientBrokerdetails) -> BrokerTransport:
    node = broker_details.execution_node
    if not node:
        raise ProxyRoutingRequiredError("No execution node assigned to broker details.")
    return BrokerTransport(broker_details=broker_details, execution_node=node)
