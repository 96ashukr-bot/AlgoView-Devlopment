from __future__ import annotations

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from main.execution_node_views import ClientExecutionNodeSerializer
from main.models import AwsAmiNodeClaim, User
from main.permissions import can_access_client_record
from main.services.aws_ami_nodes import create_or_replace_claim, register_ami_agent, verify_registered_ami_proxy
from main.services.aws_instance_identity import verify_aws_instance_identity


def _claim_payload(claim):
    if not claim:
        return None
    if claim.status == AwsAmiNodeClaim.STATUS_PENDING and claim.expires_at <= timezone.now():
        claim.status = AwsAmiNodeClaim.STATUS_EXPIRED
        claim.save(update_fields=["status", "updated_at"])
    return {
        "id": claim.id,
        "public_ip": str(claim.public_ip),
        "node_name": claim.node_name,
        "status": claim.status,
        "expires_at": claim.expires_at,
        "activated_at": claim.activated_at,
        "agent_version": claim.agent_version,
        "instance_id": claim.instance_id,
        "ami_id": claim.ami_id,
        "region": claim.region,
        "architecture": claim.architecture,
        "execution_node_id": claim.execution_node_id,
    }


class ClientAwsAmiNodeClaimAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def _client(self, request):
        client_id = request.query_params.get("client") or request.data.get("client")
        if not client_id:
            return request.user
        if not can_access_client_record(request.user, client_id):
            raise PermissionDenied("You do not have access to this client.")
        return User.objects.get(pk=client_id)

    def get(self, request):
        client = self._client(request)
        claim = AwsAmiNodeClaim.objects.filter(client=client).select_related("execution_node").first()
        node = claim.execution_node if claim and claim.execution_node_id else None
        return Response({"enabled": settings.AWS_AMI_NODE_ENABLED, "claim": _claim_payload(claim), "node": ClientExecutionNodeSerializer(node, context={"client": client}).data if node else None})

    def post(self, request):
        client = self._client(request)
        try:
            claim = create_or_replace_claim(
                client=client,
                created_by=request.user,
                public_ip=request.data.get("public_ip"),
                node_name=str(request.data.get("node_name") or "").strip(),
            )
        except ValidationError as exc:
            return Response({"detail": "; ".join(exc.messages)}, status=status.HTTP_400_BAD_REQUEST)
        return Response({"enabled": True, "claim": _claim_payload(claim)}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        client = self._client(request)
        claim = AwsAmiNodeClaim.objects.filter(client=client).first()
        if not claim:
            return Response({"status": "missing"})
        if claim.status == AwsAmiNodeClaim.STATUS_ACTIVATED:
            return Response({"detail": "Release the assigned execution node instead."}, status=status.HTTP_400_BAD_REQUEST)
        claim.status = AwsAmiNodeClaim.STATUS_CANCELLED
        claim.save(update_fields=["status", "updated_at"])
        return Response({"status": "cancelled"})


class AwsAmiNodeRegisterAPIView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def _source_ip(self, request):
        remote_ip = str(request.META.get("REMOTE_ADDR") or "").strip()
        if remote_ip in settings.AWS_AMI_TRUSTED_PROXY_IPS:
            real_ip = str(request.META.get("HTTP_X_REAL_IP") or "").strip()
            forwarded = str(request.META.get("HTTP_X_FORWARDED_FOR") or "").split(",")[0].strip()
            return real_ip or forwarded or remote_ip
        return remote_ip

    def post(self, request):
        if not settings.AWS_AMI_NODE_ENABLED:
            return Response({"status": "disabled"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        source_ip = self._source_ip(request)
        throttle_key = f"aws-ami-register:{source_ip}"
        attempts = int(cache.get(throttle_key, 0) or 0) + 1
        cache.set(throttle_key, attempts, timeout=60)
        if attempts > 12:
            return Response({"status": "failed", "message": "Registration rate limit exceeded."}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        try:
            identity = verify_aws_instance_identity(request.data.get("instance_identity_pkcs7"))
            claim, node = register_ami_agent(
                source_ip=source_ip,
                proxy_username=str(request.data.get("proxy_username") or ""),
                proxy_password=str(request.data.get("proxy_password") or ""),
                metadata={**identity, "agent_version": request.data.get("agent_version")},
            )
        except ValidationError as exc:
            message = "; ".join(exc.messages)
            response_status = status.HTTP_404_NOT_FOUND if "No pending" in message else status.HTTP_400_BAD_REQUEST
            return Response({"status": "waiting" if response_status == 404 else "failed", "message": message}, status=response_status)

        verification = verify_registered_ami_proxy(node)
        node.refresh_from_db()
        return Response({
            "status": "activated",
            "node_id": node.id,
            "public_ip": str(node.ip_address),
            "proxy_verified": node.proxy_public_ip_verified,
            "verification": verification,
            "claim_id": claim.id,
        })
