from __future__ import annotations

import logging
from typing import Any
from urllib.parse import quote

import requests
from django.conf import settings
from django.utils import timezone

from main.models import ExecutionNode

logger = logging.getLogger("main.execution_proxy")

PUBLIC_IP_ENDPOINTS = (
    "https://api.ipify.org?format=json",
    "https://ifconfig.me/ip",
    "https://checkip.amazonaws.com",
)


def _normalise_protocol(protocol: str | None) -> str:
    protocol = (protocol or ExecutionNode.PROXY_PROTOCOL_HTTP).strip().lower()
    if protocol not in {ExecutionNode.PROXY_PROTOCOL_HTTP, ExecutionNode.PROXY_PROTOCOL_HTTPS, ExecutionNode.PROXY_PROTOCOL_SOCKS5}:
        raise ValueError(f"Unsupported proxy protocol: {protocol}")
    return protocol


def _build_proxy_url(execution_node: ExecutionNode, *, mask_password: bool = False) -> str:
    protocol = _normalise_protocol(execution_node.proxy_protocol)
    host = (execution_node.proxy_host or "").strip()
    port = execution_node.proxy_port
    if not host or not port:
        raise ValueError("Proxy host and port are required.")

    username = (execution_node.proxy_username or "").strip()
    password = execution_node.get_proxy_password() if hasattr(execution_node, "get_proxy_password") else execution_node.proxy_password
    password = (password or "").strip()
    auth = ""
    if username:
        safe_username = quote(username, safe="")
        safe_password = "*****" if mask_password else quote(password, safe="")
        auth = f"{safe_username}:{safe_password}@" if password else f"{safe_username}@"
    return f"{protocol}://{auth}{host}:{port}"


def build_requests_proxy_config(execution_node: ExecutionNode) -> dict[str, str]:
    proxy_url = _build_proxy_url(execution_node)
    return {"http": proxy_url, "https": proxy_url}


def mask_proxy_url(execution_node: ExecutionNode) -> str:
    try:
        return _build_proxy_url(execution_node, mask_password=True)
    except ValueError:
        return "<proxy-not-configured>"


def _parse_public_ip_response(url: str, response: requests.Response) -> str:
    if "api.ipify.org" in url:
        return str(response.json().get("ip") or "").strip()
    return response.text.strip()


def verify_proxy_public_ip(execution_node: ExecutionNode) -> dict[str, Any]:
    expected_ip = str(execution_node.ip_address or "").strip()
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

    timeout = getattr(settings, "NODE_REQUEST_TIMEOUT", 10)
    last_error = ""
    for url in PUBLIC_IP_ENDPOINTS:
        try:
            response = requests.get(url, proxies=proxies, timeout=timeout)
            response.raise_for_status()
            actual_ip = _parse_public_ip_response(url, response)
            if not actual_ip:
                raise ValueError("Public IP endpoint returned an empty response.")
            matched = actual_ip == expected_ip
            execution_node.proxy_last_seen_ip = actual_ip
            execution_node.proxy_last_verified_at = timezone.now()
            execution_node.proxy_public_ip_verified = matched
            execution_node.proxy_last_error = "" if matched else f"Expected {expected_ip}, got {actual_ip}."
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
                    "message": "Proxy public IP verified." if matched else execution_node.proxy_last_error,
                }
            )
            return result
        except Exception as exc:  # noqa: BLE001 - every endpoint is a fallback attempt.
            last_error = str(exc)
            logger.warning("Proxy public IP verification endpoint failed", extra={"node_id": execution_node.node_id, "endpoint": url})

    execution_node.proxy_public_ip_verified = False
    execution_node.proxy_last_verified_at = timezone.now()
    execution_node.proxy_last_error = last_error or "Proxy public IP verification failed."
    execution_node.save(update_fields=["proxy_public_ip_verified", "proxy_last_verified_at", "proxy_last_error", "updated_at"])
    result["message"] = execution_node.proxy_last_error
    return result
