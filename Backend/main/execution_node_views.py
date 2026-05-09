from __future__ import annotations

import logging
import time
import uuid

import requests
from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import serializers, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.brokers import get_broker_adapter
from main.models import ClientBrokerdetails, ExecutionNode, ExecutionNodeLog, ExecutionOrderJob, User
from main.permissions import is_admin_or_superadmin
from main.services.execution_nodes import assign_execution_node_to_client, release_execution_node
from main.services.execution_router import route_order_to_execution_node
from main.services.node_security import verify_node_signature

logger = logging.getLogger("main.execution_node")


class ExecutionNodeSerializer(serializers.ModelSerializer):
    assigned_client_email = serializers.EmailField(source="assigned_client.email", read_only=True)

    class Meta:
        model = ExecutionNode
        fields = (
            "id",
            "name",
            "ip_address",
            "provider",
            "server_url",
            "node_id",
            "assigned_client",
            "assigned_client_email",
            "status",
            "is_active",
            "is_verified_with_broker",
            "last_heartbeat",
            "last_seen_ip",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("last_heartbeat", "last_seen_ip", "created_at", "updated_at")


class ClientExecutionNodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionNode
        fields = (
            "id",
            "name",
            "ip_address",
            "provider",
            "server_url",
            "node_id",
            "status",
            "is_active",
            "is_verified_with_broker",
            "last_heartbeat",
            "last_seen_ip",
            "created_at",
            "updated_at",
        )
        read_only_fields = (
            "id",
            "status",
            "is_verified_with_broker",
            "last_heartbeat",
            "last_seen_ip",
            "created_at",
            "updated_at",
        )


class ExecutionOrderJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = ExecutionOrderJob
        fields = (
            "id",
            "client",
            "broker_details",
            "execution_node",
            "symbol",
            "token",
            "exchange",
            "product",
            "order_type",
            "transaction_type",
            "quantity",
            "price",
            "trigger_price",
            "status",
            "request_payload",
            "node_response",
            "broker_response",
            "error_message",
            "retry_count",
            "idempotency_key",
            "created_at",
            "updated_at",
        )
        read_only_fields = fields


def _require_node_admin(user):
    if not is_admin_or_superadmin(user):
        raise PermissionDenied("Only admin users can manage execution nodes.")


class ExecutionNodeListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_node_admin(request.user)
        queryset = ExecutionNode.objects.select_related("assigned_client").order_by("-id")
        return Response({"results": ExecutionNodeSerializer(queryset, many=True).data})

    def post(self, request):
        _require_node_admin(request.user)
        serializer = ExecutionNodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        node = serializer.save()
        raw_secret = request.data.get("node_secret")
        if raw_secret:
            node.set_node_secret(raw_secret)
            node.save(update_fields=["node_secret", "updated_at"])
        node.mark_log("created", "Execution node created via API.")
        return Response(ExecutionNodeSerializer(node).data, status=status.HTTP_201_CREATED)


class ExecutionNodeAssignAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        _require_node_admin(request.user)
        client = User.objects.get(pk=request.data.get("client_id"))
        node = ExecutionNode.objects.get(pk=request.data.get("node_id"))
        assigned = assign_execution_node_to_client(client, node)
        return Response(ExecutionNodeSerializer(assigned).data)


class ExecutionNodeDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, node_id):
        _require_node_admin(request.user)
        node = ExecutionNode.objects.select_related("assigned_client").get(pk=node_id)
        return Response(ExecutionNodeSerializer(node).data)

    def patch(self, request, node_id):
        _require_node_admin(request.user)
        node = ExecutionNode.objects.get(pk=node_id)
        serializer = ExecutionNodeSerializer(node, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        node = serializer.save()
        if request.data.get("node_secret"):
            node.set_node_secret(request.data["node_secret"])
            node.save(update_fields=["node_secret", "updated_at"])
        node.mark_log("updated", "Execution node updated via API.")
        return Response(ExecutionNodeSerializer(node).data)


class ExecutionNodeReleaseAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        _require_node_admin(request.user)
        client = User.objects.get(pk=request.data.get("client_id"))
        node = release_execution_node(client)
        return Response({"status": "released", "node_id": node.id if node else None})


class ExecutionNodeHealthAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, node_id):
        _require_node_admin(request.user)
        node = ExecutionNode.objects.get(pk=node_id)
        try:
            response = requests.get(node.server_url.rstrip("/") + "/api/node/health/", timeout=settings.NODE_REQUEST_TIMEOUT)
            payload = response.json() if response.content else {}
            return Response({"status": "success" if response.ok else "failed", "node": ExecutionNodeSerializer(node).data, "health": payload})
        except requests.RequestException as exc:
            return Response({"status": "failed", "node": ExecutionNodeSerializer(node).data, "message": str(exc)}, status=status.HTTP_200_OK)


class ClientExecutionNodeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        node = ExecutionNode.objects.filter(assigned_client=request.user).first()
        return Response({"node": ClientExecutionNodeSerializer(node).data if node else None})

    @transaction.atomic
    def post(self, request):
        if ExecutionNode.objects.filter(assigned_client=request.user).exists():
            return Response(
                {"detail": "This client already has an execution IP. Update the existing IP instead."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = ClientExecutionNodeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        node = serializer.save(
            assigned_client=request.user,
            status=ExecutionNode.STATUS_ASSIGNED,
            is_verified_with_broker=False,
        )
        raw_secret = request.data.get("node_secret")
        if raw_secret:
            node.set_node_secret(raw_secret)
            node.save(update_fields=["node_secret", "updated_at"])
        ClientBrokerdetails.objects.filter(client=request.user).update(execution_node=node)
        node.mark_log("client_created", "Execution node created by assigned client.", client=request.user)
        return Response(ClientExecutionNodeSerializer(node).data, status=status.HTTP_201_CREATED)

    @transaction.atomic
    def patch(self, request):
        node = ExecutionNode.objects.select_for_update().filter(assigned_client=request.user).first()
        if not node:
            return Response({"detail": "No execution IP is assigned to this client."}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClientExecutionNodeSerializer(node, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        node = serializer.save()
        raw_secret = request.data.get("node_secret")
        if raw_secret:
            node.set_node_secret(raw_secret)
            node.save(update_fields=["node_secret", "updated_at"])
        ClientBrokerdetails.objects.filter(client=request.user).update(execution_node=node)
        node.mark_log("client_updated", "Execution node updated by assigned client.", client=request.user)
        return Response(ClientExecutionNodeSerializer(node).data)

    def delete(self, request):
        node = release_execution_node(request.user)
        return Response({"status": "released", "node_id": node.id if node else None})


class ExecutionOrderJobListAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        _require_node_admin(request.user)
        queryset = ExecutionOrderJob.objects.select_related("client", "execution_node", "broker_details").order_by("-id")
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        return Response({"results": ExecutionOrderJobSerializer(queryset[:200], many=True).data})


class ExecutionOrderJobRetryAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, job_id):
        _require_node_admin(request.user)
        job = ExecutionOrderJob.objects.select_related("client", "broker_details").get(pk=job_id)
        result = route_order_to_execution_node(job.client, job.broker_details, {**job.request_payload.get("order", {}), "idempotency_key": str(uuid.uuid4())})
        return Response(result)


class NodeHealthAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        return Response({"status": "ok", "node_id": settings.ALGOVIEW_NODE_ID, "node_mode": settings.ALGOVIEW_NODE_MODE})


class NodePublicIPAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request):
        try:
            ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
        except requests.RequestException:
            ip = request.META.get("REMOTE_ADDR")
        return Response({"public_ip": ip})


class NodeHeartbeatAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        node_id = request.headers.get("X-ALGOVIEW-NODE-ID") or request.data.get("node_id") or settings.ALGOVIEW_NODE_ID
        secret = settings.ALGOVIEW_NODE_SECRET
        verify_node_signature(
            secret,
            request.headers.get("X-ALGOVIEW-TIMESTAMP"),
            request.data,
            request.headers.get("X-ALGOVIEW-SIGNATURE"),
        )
        node = ExecutionNode.objects.filter(node_id=node_id).first()
        if node:
            node.last_heartbeat = timezone.now()
            node.last_seen_ip = request.META.get("HTTP_X_FORWARDED_FOR", request.META.get("REMOTE_ADDR", "")).split(",")[0]
            node.status = ExecutionNode.STATUS_ONLINE if node.assigned_client_id else ExecutionNode.STATUS_FREE
            node.save(update_fields=["last_heartbeat", "last_seen_ip", "status", "updated_at"])
            node.mark_log("heartbeat", "Execution node heartbeat received.", metadata={"ip": node.last_seen_ip})
        return Response({"status": "ok", "node_id": node_id})


class NodePlaceOrderAPIView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        idempotency_key = request.headers.get("X-ALGOVIEW-IDEMPOTENCY-KEY")
        if not idempotency_key:
            return Response({"status": "failed", "message": "Missing idempotency key."}, status=status.HTTP_400_BAD_REQUEST)
        verify_node_signature(
            settings.ALGOVIEW_NODE_SECRET,
            request.headers.get("X-ALGOVIEW-TIMESTAMP"),
            request.data,
            request.headers.get("X-ALGOVIEW-SIGNATURE"),
        )
        cache_key = f"execution-node:idempotency:{idempotency_key}"
        if not cache.add(cache_key, timezone.now().isoformat(), timeout=86400):
            return Response({"status": "duplicate", "message": "Duplicate idempotency key rejected."}, status=status.HTTP_409_CONFLICT)

        broker_details = ClientBrokerdetails.objects.select_related("client", "broker_name").get(pk=request.data.get("broker_details_id"))
        adapter = get_broker_adapter(broker_details)
        validation = adapter.validate_credentials()
        if validation.get("status") != "success":
            return Response({"status": "failed", "message": validation.get("message")}, status=status.HTTP_400_BAD_REQUEST)
        try:
            broker_response = adapter.place_order(request.data)
            safe_response = {
                "status": "placed" if str(broker_response.get("status", broker_response.get("data", {}).get("status", ""))).lower() in {"success", "complete", "completed", "open"} else "accepted",
                "broker_response": broker_response,
            }
            node = ExecutionNode.objects.filter(node_id=settings.ALGOVIEW_NODE_ID).first()
            if node:
                ExecutionNodeLog.objects.create(
                    execution_node=node,
                    client=broker_details.client,
                    event_type="node_order",
                    message="Node processed order request.",
                    metadata={"idempotency_key": idempotency_key},
                )
            return Response(safe_response)
        except Exception as exc:
            logger.exception("Node order placement failed")
            return Response({"status": "failed", "message": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
