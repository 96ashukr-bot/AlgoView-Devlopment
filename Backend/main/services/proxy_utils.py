from __future__ import annotations

import logging
import ipaddress
import unicodedata
from typing import Any
from urllib.parse import quote

import requests
from django.conf import settings
from django.utils import timezone

from main.models import ExecutionNode

logger = logging.getLogger("main.execution_proxy")

PUBLIC_IP_ENDPOINTS = (
    "https://api.ipify.org?format=json",
    "https://api64.ipify.org?format=json",
    "https://ifconfig.me/ip",
    "https://checkip.amazonaws.com",
)

PROXY_VERIFY_CONNECT_TIMEOUT_SECONDS = 3
PROXY_VERIFY_READ_TIMEOUT_SECONDS = 5
PROXY_VERIFY_MIN_SUCCESSFUL_CHECKS = 2


def _clean_proxy_value(value: str | None) -> str:
    """Remove invisible copy/paste artifacts that make proxy URLs unparsable."""
    cleaned = unicodedata.normalize("NFKC", str(value or ""))
    cleaned = "".join(ch for ch in cleaned if unicodedata.category(ch) not in {"Cf", "Cc"})
    return cleaned.strip()


def _normalise_protocol(protocol: str | None) -> str:
    protocol = _clean_proxy_value(protocol or ExecutionNode.PROXY_PROTOCOL_HTTP).lower()
    if protocol not in {ExecutionNode.PROXY_PROTOCOL_HTTP, ExecutionNode.PROXY_PROTOCOL_HTTPS, ExecutionNode.PROXY_PROTOCOL_SOCKS5}:
        raise ValueError(f"Unsupported proxy protocol: {protocol}")
    return protocol


def _strip_ipv6_brackets(host: str) -> str:
    host = _clean_proxy_value(host)
    if host.startswith("[") and host.endswith("]"):
        return host[1:-1]
    return host


def _format_proxy_host(host: str) -> str:
    host = _strip_ipv6_brackets(host)
    try:
        parsed = ipaddress.ip_address(host)
    except ValueError:
        return host
    if parsed.version == 6:
        return f"[{parsed.compressed}]"
    return parsed.compressed


def _normalize_ip(value: str | None) -> str:
    value = _clean_proxy_value(value)
    if not value:
        return ""
    try:
        return ipaddress.ip_address(_strip_ipv6_brackets(value)).compressed
    except ValueError:
        return value


def _build_proxy_url(execution_node: ExecutionNode, *, mask_password: bool = False) -> str:
    protocol = _normalise_protocol(execution_node.proxy_protocol)
    host = _clean_proxy_value(execution_node.proxy_host)
    port = execution_node.proxy_port
    if not host or not port:
        raise ValueError("Proxy host and port are required.")

    username = _clean_proxy_value(execution_node.proxy_username)
    password = execution_node.get_proxy_password() if hasattr(execution_node, "get_proxy_password") else execution_node.proxy_password
    password = _clean_proxy_value(password)
    auth = ""
    if username:
        safe_username = quote(username, safe="")
        safe_password = "*****" if mask_password else quote(password, safe="")
        auth = f"{safe_username}:{safe_password}@" if password else f"{safe_username}@"
    return f"{protocol}://{auth}{_format_proxy_host(host)}:{port}"


def build_requests_proxy_config(execution_node: ExecutionNode) -> dict[str, str]:
    proxy_url = _build_proxy_url(execution_node)
    return {"http": proxy_url, "https": proxy_url}


def mask_proxy_url(execution_node: ExecutionNode) -> str:
    try:
        return _build_proxy_url(execution_node, mask_password=True)
    except ValueError:
        return "<proxy-not-configured>"


def _parse_public_ip_response(url: str, response: requests.Response) -> str:
    if "ipify.org" in url:
        return str(response.json().get("ip") or "").strip()
    return response.text.strip()


def verify_proxy_public_ip(execution_node: ExecutionNode) -> dict[str, Any]:
    expected_ip = _normalize_ip(str(execution_node.ip_address or ""))
    result: dict[str, Any] = {
        "status": "failed",
        "expected_ip": expected_ip,
        "actual_ip": None,
        "message": "",
        "proxy": mask_proxy_url(execution_node),
    }
    if execution_node.execution_type != ExecutionNode.EXECUTION_TYPE_PROXY:
        result["message"] = "Proxy verification is only available for proxy execution nodes."
        return result

    try:
        proxies = build_requests_proxy_config(execution_node)
    except ValueError as exc:
        result["message"] = str(exc)
        execution_node.proxy_public_ip_verified = False
        execution_node.proxy_last_error = str(exc)
        execution_node.proxy_last_verified_at = timezone.now()
        execution_node.save(update_fields=["proxy_public_ip_verified", "proxy_last_error", "proxy_last_verified_at", "updated_at"])
        return result

    configured_timeout = getattr(settings, "NODE_REQUEST_TIMEOUT", 10)
    timeout = (
        min(PROXY_VERIFY_CONNECT_TIMEOUT_SECONDS, configured_timeout),
        min(PROXY_VERIFY_READ_TIMEOUT_SECONDS, configured_timeout),
    )
    last_error = ""
    observed_ips: list[str] = []
    for url in PUBLIC_IP_ENDPOINTS:
        try:
            response = requests.get(url, proxies=proxies, timeout=timeout)
            response.raise_for_status()
            actual_ip = _normalize_ip(_parse_public_ip_response(url, response))
            if not actual_ip:
                raise ValueError("Public IP endpoint returned an empty response.")
            observed_ips.append(actual_ip)
            if len(observed_ips) >= PROXY_VERIFY_MIN_SUCCESSFUL_CHECKS:
                break
        except Exception as exc:  # noqa: BLE001 - every endpoint is a fallback attempt.
            last_error = str(exc)
            logger.warning("Proxy public IP verification endpoint failed", extra={"node_id": execution_node.node_id, "endpoint": url})

    if observed_ips:
        unique_ips = sorted(set(observed_ips))
        matched = len(unique_ips) == 1 and unique_ips[0] == expected_ip
        actual_ip = unique_ips[0] if len(unique_ips) == 1 else ", ".join(unique_ips)
        if matched:
            message = "Proxy public IP verified."
        elif len(unique_ips) > 1:
            message = f"Proxy route is rotating public IPs. Expected {expected_ip}, got {actual_ip}."
        else:
            message = f"Expected {expected_ip}, got {actual_ip}."
        execution_node.proxy_last_seen_ip = unique_ips[-1]
        execution_node.proxy_last_verified_at = timezone.now()
        execution_node.proxy_public_ip_verified = matched
        execution_node.proxy_last_error = "" if matched else message
        execution_node.save(
            update_fields=[
                "proxy_last_seen_ip",
                "proxy_last_verified_at",
                "proxy_public_ip_verified",
                "proxy_last_error",
                "updated_at",
            ]
        )
        result.update(
            {
                "status": "success" if matched else "failed",
                "actual_ip": actual_ip,
                "message": message,
            }
        )
        return result

    execution_node.proxy_public_ip_verified = False
    execution_node.proxy_last_verified_at = timezone.now()
    execution_node.proxy_last_error = last_error or "Proxy public IP verification failed."
    execution_node.save(update_fields=["proxy_public_ip_verified", "proxy_last_verified_at", "proxy_last_error", "updated_at"])
    result["message"] = execution_node.proxy_last_error
    return result
