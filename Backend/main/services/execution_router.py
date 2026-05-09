from __future__ import annotations

import logging
import time
import uuid
from decimal import Decimal
from typing import Any
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction

from main.models import ClientBrokerdetails, ExecutionNode, ExecutionOrderJob, User
from main.brokers import get_broker_adapter
from main.services.execution_nodes import get_execution_node_for_client
from main.services.node_security import generate_node_signature
from main.services.proxy_utils import build_requests_proxy_config, mask_proxy_url

logger = logging.getLogger("main.execution_router")


def _decimal_or_none(value):
    if value in (None, ""):
        return None
    try:
        return Decimal(str(value))
    except Exception:
        return None


def _safe_job_payload(order_payload: dict[str, Any], broker_details: ClientBrokerdetails) -> dict[str, Any]:
    return {
        "client_id": broker_details.client_id,
        "broker_details_id": broker_details.id,
        "broker": getattr(getattr(broker_details, "broker_name", None), "broker_name", None),
        "order": order_payload,
    }


def _extract_job_fields(order_payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "symbol": order_payload.get("symbol") or order_payload.get("tradingsymbol") or order_payload.get("trading_symbol"),
        "token": order_payload.get("token") or order_payload.get("instrument_token") or order_payload.get("symboltoken"),
        "exchange": order_payload.get("exchange") or order_payload.get("Exchange"),
        "product": order_payload.get("product") or order_payload.get("product_type"),
        "order_type": order_payload.get("order_type") or order_payload.get("ordertype"),
        "transaction_type": order_payload.get("transaction_type"),
        "quantity": int(order_payload.get("quantity") or 0) if str(order_payload.get("quantity") or "").isdigit() else None,
        "price": _decimal_or_none(order_payload.get("price")),
        "trigger_price": _decimal_or_none(order_payload.get("trigger_price") or order_payload.get("triggerPrice")),
    }


def route_order_to_execution_node(client: User, broker_details: ClientBrokerdetails, order_payload: dict[str, Any]) -> dict[str, Any]:
    if not client or not getattr(client, "id", None):
        raise ValidationError("Client is required for execution routing.")
    if not broker_details or broker_details.client_id != client.id:
        raise ValidationError("Broker details do not belong to the selected client.")

    node = broker_details.execution_node or get_execution_node_for_client(client)
    if not node:
        raise ValidationError("No execution node assigned to this client.")
    if node.assigned_client_id and node.assigned_client_id != client.id:
        raise ValidationError("Execution node is not assigned to this client.")
    if not node.is_active or node.status in {ExecutionNode.STATUS_DISABLED, ExecutionNode.STATUS_MAINTENANCE, ExecutionNode.STATUS_OFFLINE}:
        raise ValidationError("Execution node is not available for trading.")
    if not node.is_verified_with_broker:
        raise ValidationError("Execution node is not verified with broker for this client.")
    if node.execution_type == ExecutionNode.EXECUTION_TYPE_PROXY and not node.proxy_public_ip_verified:
        raise ValidationError("Execution proxy public IP is not verified.")

    idempotency_key = str(order_payload.get("idempotency_key") or uuid.uuid4())
    request_payload = _safe_job_payload(order_payload, broker_details)
    job_fields = _extract_job_fields(order_payload)
    try:
        with transaction.atomic():
            job, created = ExecutionOrderJob.objects.get_or_create(
                idempotency_key=idempotency_key,
                defaults={
                    "client": client,
                    "broker_details": broker_details,
                    "execution_node": node,
                    "execution_type": node.execution_type,
                    "request_payload": request_payload,
                    "proxy_metadata": {"proxy": mask_proxy_url(node), "static_ip": str(node.ip_address)} if node.execution_type == ExecutionNode.EXECUTION_TYPE_PROXY else {},
                    **job_fields,
                },
            )
            if not created and job.status in {
                ExecutionOrderJob.STATUS_SENT_TO_NODE,
                ExecutionOrderJob.STATUS_ACCEPTED_BY_NODE,
                ExecutionOrderJob.STATUS_PLACED,
            }:
                return {"status": "duplicate", "job_id": job.id, "job_status": job.status}
            if not created:
                job.retry_count += 1
                job.request_payload = request_payload
                job.execution_type = node.execution_type
                job.proxy_metadata = {"proxy": mask_proxy_url(node), "static_ip": str(node.ip_address)} if node.execution_type == ExecutionNode.EXECUTION_TYPE_PROXY else {}
                job.save(update_fields=["retry_count", "request_payload", "execution_type", "proxy_metadata", "updated_at"])
    except IntegrityError:
        job = ExecutionOrderJob.objects.get(idempotency_key=idempotency_key)
        return {"status": "duplicate", "job_id": job.id, "job_status": job.status}

    if node.execution_type == ExecutionNode.EXECUTION_TYPE_PROXY:
        try:
            adapter = get_broker_adapter(broker_details)
            if not getattr(adapter, "supports_proxy", False):
                raise ValidationError(
                    "This broker adapter does not currently support proxy-based execution. "
                    "Use VPS node mode or implement direct HTTP/proxy support."
                )
            proxy_config = build_requests_proxy_config(node)
            job.status = ExecutionOrderJob.STATUS_PROXY_ROUTING
            job.save(update_fields=["status", "updated_at"])
            validation = adapter.validate_credentials(proxy_config=proxy_config)
            if validation.get("status") != "success":
                raise ValidationError(validation.get("message") or "Broker credentials are invalid.")
            broker_response = adapter.place_order(request_payload, proxy_config=proxy_config)
            response_status = str(broker_response.get("status", broker_response.get("data", {}).get("status", ""))).lower()
            job.broker_response = broker_response
            job.status = ExecutionOrderJob.STATUS_PLACED if response_status in {"success", "complete", "completed", "open", "placed"} else ExecutionOrderJob.STATUS_REJECTED
            if job.status == ExecutionOrderJob.STATUS_REJECTED:
                job.error_message = broker_response.get("message") or broker_response.get("data", {}).get("message") or "Broker rejected proxy-routed order."
            job.save(update_fields=["broker_response", "status", "error_message", "updated_at"])
            node.mark_log("proxy_order_routed", f"Order job {job.id} routed through assigned proxy.", client=client, metadata={"status": job.status, "proxy": mask_proxy_url(node)})
            return {"status": job.status, "job_id": job.id, "message": job.error_message}
        except ValidationError:
            job.status = ExecutionOrderJob.STATUS_FAILED
            job.error_message = "Proxy order validation failed."
            job.save(update_fields=["status", "error_message", "updated_at"])
            raise
        except Exception as exc:  # noqa: BLE001
            job.status = ExecutionOrderJob.STATUS_FAILED
            job.error_message = str(exc)
            job.save(update_fields=["status", "error_message", "updated_at"])
            logger.exception("Proxy-routed broker order failed", extra={"job_id": job.id, "node_id": node.node_id})
            return {"status": "failed", "job_id": job.id, "message": "Proxy-routed broker order failed."}

    node_secret = node.get_node_secret()
    if not node_secret:
        raise ValidationError("Execution node secret is not configured.")
    if not node.server_url or not node.node_id:
        raise ValidationError("Execution node server URL or node ID is not configured.")

    timestamp = str(int(time.time()))
    signature = generate_node_signature(node_secret, timestamp, request_payload)
    headers = {
        "Content-Type": "application/json",
        "X-ALGOVIEW-NODE-ID": node.node_id,
        "X-ALGOVIEW-TIMESTAMP": timestamp,
        "X-ALGOVIEW-SIGNATURE": signature,
        "X-ALGOVIEW-IDEMPOTENCY-KEY": idempotency_key,
    }
    url = urljoin(node.server_url.rstrip("/") + "/", "api/node/place-order/")

    try:
        job.status = ExecutionOrderJob.STATUS_SENT_TO_NODE
        job.save(update_fields=["status", "updated_at"])
        response = requests.post(url, json=request_payload, headers=headers, timeout=settings.NODE_REQUEST_TIMEOUT)
        response_payload = response.json() if response.content else {}
        job.node_response = response_payload
        broker_response = response_payload.get("broker_response") if isinstance(response_payload, dict) else None
        job.broker_response = broker_response
        if response.ok and str(response_payload.get("status", "")).lower() in {"accepted", "placed", "success"}:
            job.status = ExecutionOrderJob.STATUS_PLACED if response_payload.get("broker_response") else ExecutionOrderJob.STATUS_ACCEPTED_BY_NODE
        else:
            job.status = ExecutionOrderJob.STATUS_REJECTED if response.status_code < 500 else ExecutionOrderJob.STATUS_FAILED
            job.error_message = response_payload.get("message") if isinstance(response_payload, dict) else response.text[:1000]
        job.save(update_fields=["node_response", "broker_response", "status", "error_message", "updated_at"])
        node.mark_log("order_routed", f"Order job {job.id} routed to execution node.", client=client, metadata={"status": job.status})
        return {"status": job.status, "job_id": job.id, "message": job.error_message}
    except requests.Timeout:
        job.status = ExecutionOrderJob.STATUS_FAILED
        job.error_message = "Execution node request timed out."
        job.save(update_fields=["status", "error_message", "updated_at"])
        node.mark_log("order_timeout", job.error_message, client=client, metadata={"job_id": job.id})
        return {"status": "failed", "job_id": job.id, "message": job.error_message}
    except requests.RequestException as exc:
        job.status = ExecutionOrderJob.STATUS_FAILED
        job.error_message = str(exc)
        job.save(update_fields=["status", "error_message", "updated_at"])
        logger.exception("Execution node request failed", extra={"job_id": job.id, "node_id": node.node_id})
        return {"status": "failed", "job_id": job.id, "message": "Execution node request failed."}
