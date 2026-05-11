from __future__ import annotations

import logging
from urllib.parse import urlparse

import requests
from django.conf import settings

from main.services.broker_transport import ProxyRoutingRequiredError

logger = logging.getLogger("main.egress_guard")

BROKER_HOST_FRAGMENTS = (
    "angelbroking.com",
    "smartapi.angelone.in",
    "apiconnect.angelbroking.com",
    "upstox.com",
    "api-t1.fyers.in",
    "fyers.in",
    "5paisa.com",
    "dhan.co",
    "kite.trade",
    "zerodha.com",
    "aliceblueonline.com",
    "ant.aliceblueonline.com",
)

PUBLIC_INSTRUMENT_MASTER_PATHS = (
    ("margincalculator.angelbroking.com", "/OpenAPI_File/files/OpenAPIScripMaster.json"),
    ("images.dhan.co", "/api-data/api-scrip-master.csv"),
    ("assets.upstox.com", "/market-quote/instruments/exchange/"),
    ("public.fyers.in", "/sym_details/"),
    ("Openapi.5paisa.com".lower(), "/VendorsAPI/Service1.svc/ScripMaster/segment/"),
)

_ORIGINAL_REQUEST = None
_INSTALLED = False


def _is_broker_url(url: str) -> bool:
    hostname = (urlparse(str(url)).hostname or "").lower()
    return any(fragment in hostname for fragment in BROKER_HOST_FRAGMENTS)


def _is_public_instrument_master_url(url: str) -> bool:
    parsed = urlparse(str(url))
    hostname = (parsed.hostname or "").lower()
    path = parsed.path or ""
    return any(hostname == allowed_host and path.startswith(allowed_path) for allowed_host, allowed_path in PUBLIC_INSTRUMENT_MASTER_PATHS)


def _has_proxy(session: requests.Session, kwargs: dict) -> bool:
    explicit = kwargs.get("proxies")
    if explicit:
        return bool(explicit.get("http") or explicit.get("https"))
    return bool(session.proxies.get("http") or session.proxies.get("https"))


def enforce_broker_proxy_for_requests() -> None:
    global _ORIGINAL_REQUEST, _INSTALLED
    if _INSTALLED:
        return
    if not getattr(settings, "ALGOVIEW_ENFORCE_BROKER_PROXY_GUARD", True):
        return

    _ORIGINAL_REQUEST = requests.sessions.Session.request

    def guarded_request(self, method, url, **kwargs):
        if _is_broker_url(url) and not _is_public_instrument_master_url(url) and not _has_proxy(self, kwargs):
            logger.error("Blocked direct broker egress without proxy", extra={"method": method, "url": urlparse(str(url)).netloc})
            raise ProxyRoutingRequiredError("Direct broker egress without client proxy/static-IP route is blocked.")
        return _ORIGINAL_REQUEST(self, method, url, **kwargs)

    requests.sessions.Session.request = guarded_request
    _INSTALLED = True
