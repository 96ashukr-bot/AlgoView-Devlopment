from __future__ import annotations

import ipaddress
from datetime import timedelta

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from main.models import AwsAmiNodeClaim, ExecutionNode, User
from main.services.execution_nodes import assign_execution_node_to_client, get_execution_node_for_client
from main.services.proxy_utils import verify_proxy_public_ip


def normalize_public_ip(value) -> str:
    try:
        parsed = ipaddress.ip_address(str(value or "").strip())
    except ValueError as exc:
        raise ValidationError("Enter a valid public IPv4 address.") from exc
    if parsed.version != 4 or not parsed.is_global:
        raise ValidationError("AWS AMI nodes require a public IPv4 address.")
    return str(parsed)


@transaction.atomic
def create_or_replace_claim(*, client: User, created_by: User, public_ip: str, node_name: str = "") -> AwsAmiNodeClaim:
    if not settings.AWS_AMI_NODE_ENABLED:
        raise ValidationError("AWS AMI node onboarding is not enabled.")
    if not settings.AWS_AMI_ALLOWED_IDS:
        raise ValidationError("No approved AlgoView AMI is configured.")
    if get_execution_node_for_client(client):
        raise ValidationError("This client already has an execution node. Release it before claiming an AWS AMI node.")

    public_ip = normalize_public_ip(public_ip)
    conflicting = AwsAmiNodeClaim.objects.select_for_update().filter(public_ip=public_ip).exclude(client=client).first()
    if conflicting and conflicting.status in {AwsAmiNodeClaim.STATUS_PENDING, AwsAmiNodeClaim.STATUS_ACTIVATED}:
        raise ValidationError("This AWS public IPv4 is already claimed by another client.")
    if conflicting:
        conflicting.delete()

    claim, _ = AwsAmiNodeClaim.objects.select_for_update().get_or_create(
        client=client,
        defaults={"public_ip": public_ip, "node_name": node_name or f"{client.fullName or client.email} AWS AMI Node", "created_by": created_by, "expires_at": timezone.now()},
    )
    claim.public_ip = public_ip
    claim.node_name = (node_name or f"{client.fullName or client.email} AWS AMI Node")[:150]
    claim.created_by = created_by
    claim.status = AwsAmiNodeClaim.STATUS_PENDING
    claim.execution_node = None
    claim.expires_at = timezone.now() + timedelta(seconds=max(300, int(settings.AWS_AMI_CLAIM_TTL_SECONDS)))
    claim.activated_at = None
    claim.agent_version = None
    claim.instance_id = None
    claim.ami_id = None
    claim.region = None
    claim.architecture = None
    try:
        claim.save()
    except IntegrityError as exc:
        raise ValidationError("This AWS public IPv4 is already being claimed.") from exc
    return claim


@transaction.atomic
def register_ami_agent(*, source_ip: str, proxy_username: str, proxy_password: str, metadata: dict) -> tuple[AwsAmiNodeClaim, ExecutionNode]:
    if not settings.AWS_AMI_NODE_ENABLED:
        raise ValidationError("AWS AMI node onboarding is disabled.")
    source_ip = normalize_public_ip(source_ip)
    now = timezone.now()
    claim = AwsAmiNodeClaim.objects.select_for_update().select_related("client", "execution_node").filter(public_ip=source_ip).first()
    if claim is None:
        raise ValidationError("No pending AWS node claim exists for this public IPv4.")
    if claim.status == AwsAmiNodeClaim.STATUS_ACTIVATED and claim.execution_node_id:
        node = claim.execution_node
        if node.proxy_username != proxy_username or node.get_proxy_password() != proxy_password:
            raise ValidationError("AWS node credentials do not match the activated node.")
        return claim, node
    if claim.status != AwsAmiNodeClaim.STATUS_PENDING or claim.expires_at <= now:
        if claim.status == AwsAmiNodeClaim.STATUS_PENDING:
            claim.status = AwsAmiNodeClaim.STATUS_EXPIRED
            claim.save(update_fields=["status", "updated_at"])
        raise ValidationError("The AWS node claim has expired. Create a new claim in AlgoView.")
    if get_execution_node_for_client(claim.client):
        raise ValidationError("The client already has another execution node assigned.")
    if not (8 <= len(proxy_username) <= 128 and 24 <= len(proxy_password) <= 256):
        raise ValidationError("AMI proxy credentials do not meet security requirements.")
    instance_id = str(metadata.get("instanceId") or "")[:100]
    if AwsAmiNodeClaim.objects.exclude(pk=claim.pk).filter(instance_id=instance_id).exists():
        raise ValidationError("This AWS instance is already registered.")

    node = ExecutionNode.objects.select_for_update().filter(ip_address=source_ip).first()
    if node and (node.provider != "AWS AMI" or node.client_assignments.exists() or node.assigned_client_id):
        raise ValidationError("This public IPv4 belongs to another execution route.")
    if node is None:
        node = ExecutionNode(ip_address=source_ip)
    node.name = claim.node_name
    node.provider = "AWS AMI"
    node.execution_type = ExecutionNode.EXECUTION_TYPE_PROXY
    node.proxy_host = source_ip
    node.proxy_port = int(settings.AWS_AMI_PROXY_PORT)
    node.proxy_protocol = ExecutionNode.PROXY_PROTOCOL_HTTP
    node.proxy_username = proxy_username
    node.status = ExecutionNode.STATUS_FREE
    node.is_active = True
    node.is_verified_with_broker = False
    node.proxy_public_ip_verified = False
    node.set_proxy_password(proxy_password)
    node.full_clean()
    node.save()
    node = assign_execution_node_to_client(claim.client, node, assigned_by=claim.created_by)

    claim.status = AwsAmiNodeClaim.STATUS_ACTIVATED
    claim.execution_node = node
    claim.activated_at = now
    claim.agent_version = str(metadata.get("agent_version") or "")[:50] or None
    claim.instance_id = instance_id or None
    claim.ami_id = str(metadata.get("imageId") or "")[:100] or None
    claim.region = str(metadata.get("region") or "")[:50] or None
    claim.architecture = str(metadata.get("architecture") or "")[:30] or None
    claim.save()
    node.mark_log("aws_ami_activated", "AWS AMI execution route activated automatically.", client=claim.client, metadata={"instance_id": claim.instance_id, "ami_id": claim.ami_id, "agent_version": claim.agent_version})
    return claim, node


def verify_registered_ami_proxy(node: ExecutionNode) -> dict:
    return verify_proxy_public_ip(node)
