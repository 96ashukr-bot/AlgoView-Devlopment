from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from main.models import ClientBrokerdetails, ExecutionNode, ExecutionNodeAssignment, User


def verify_node_available(node: ExecutionNode) -> None:
    if not node:
        raise ValidationError("Execution node is required.")
    if not node.is_active or node.status == ExecutionNode.STATUS_DISABLED:
        raise ValidationError("Execution node is not active.")
    if node.status == ExecutionNode.STATUS_MAINTENANCE:
        raise ValidationError("Execution node is in maintenance mode.")
    if node.execution_type == ExecutionNode.EXECUTION_TYPE_PROXY:
        if not (node.proxy_host and node.proxy_port and node.proxy_protocol):
            raise ValidationError("Proxy execution node is missing proxy host, port, or protocol.")


def execution_node_assigned_to_client(node: ExecutionNode, client: User) -> bool:
    if not node or not client:
        return False
    return bool(
        node.assigned_client_id == client.id
        or ExecutionNodeAssignment.objects.filter(execution_node=node, client=client).exists()
    )


def _sync_legacy_primary_client(node: ExecutionNode) -> None:
    assignment = (
        ExecutionNodeAssignment.objects.filter(execution_node=node)
        .select_related("client")
        .order_by("created_at", "id")
        .first()
    )
    primary_client = assignment.client if assignment else None
    status = ExecutionNode.STATUS_ASSIGNED if primary_client else (
        ExecutionNode.STATUS_FREE if node.is_active else ExecutionNode.STATUS_DISABLED
    )
    update_fields = []
    if node.assigned_client_id != getattr(primary_client, "id", None):
        node.assigned_client = primary_client
        update_fields.append("assigned_client")
    if node.status != status:
        node.status = status
        update_fields.append("status")
    if update_fields:
        node.save(update_fields=[*update_fields, "updated_at"])


@transaction.atomic
def assign_execution_node_to_client(client: User, node: ExecutionNode, assigned_by: User | None = None) -> ExecutionNode:
    client = User.objects.select_for_update().get(pk=client.pk)
    node = ExecutionNode.objects.select_for_update().get(pk=node.pk)
    existing = ExecutionNodeAssignment.objects.select_for_update().filter(client=client).first()
    if existing and existing.execution_node_id != node.id:
        raise ValidationError("Client already has an execution node.")
    if ExecutionNode.objects.filter(assigned_client=client).exclude(pk=node.pk).exists():
        raise ValidationError("Client already has an execution node.")
    if not node.is_active:
        raise ValidationError("Inactive execution node cannot be assigned.")
    if node.execution_type == ExecutionNode.EXECUTION_TYPE_PROXY and not (node.proxy_host and node.proxy_port and node.proxy_protocol):
        raise ValidationError("Proxy execution node is missing proxy host, port, or protocol.")

    ExecutionNodeAssignment.objects.get_or_create(
        client=client,
        defaults={"execution_node": node, "assigned_by": assigned_by},
    )
    ClientBrokerdetails.objects.filter(client=client).update(execution_node=node)
    _sync_legacy_primary_client(node)
    node.refresh_from_db()
    node.mark_log("assigned", "Execution node assigned to client.", client=client, metadata={"multi_client": True})
    return node


@transaction.atomic
def release_execution_node(client: User) -> ExecutionNode | None:
    assignment = ExecutionNodeAssignment.objects.select_for_update().select_related("execution_node").filter(client=client).first()
    node = assignment.execution_node if assignment else ExecutionNode.objects.select_for_update().filter(assigned_client=client).first()
    if not node:
        ClientBrokerdetails.objects.filter(client=client).update(execution_node=None)
        return None
    if assignment:
        assignment.delete()
    ClientBrokerdetails.objects.filter(client=client).update(execution_node=None)
    _sync_legacy_primary_client(node)
    node.refresh_from_db()
    node.mark_log("released", "Execution node released from client.", client=client, metadata={"multi_client": True})
    return node


@transaction.atomic
def release_all_execution_node_clients(node: ExecutionNode) -> int:
    node = ExecutionNode.objects.select_for_update().get(pk=node.pk)
    client_ids = list(node.client_assignments.values_list("client_id", flat=True))
    if node.assigned_client_id and node.assigned_client_id not in client_ids:
        client_ids.append(node.assigned_client_id)
    ExecutionNodeAssignment.objects.filter(execution_node=node).delete()
    ClientBrokerdetails.objects.filter(client_id__in=client_ids, execution_node=node).update(execution_node=None)
    node.assigned_client = None
    node.status = ExecutionNode.STATUS_FREE if node.is_active else ExecutionNode.STATUS_DISABLED
    node.save(update_fields=["assigned_client", "status", "updated_at"])
    return len(client_ids)


def get_execution_node_for_client(client: User) -> ExecutionNode | None:
    assignment = ExecutionNodeAssignment.objects.filter(client=client).select_related("execution_node").first()
    if assignment:
        return assignment.execution_node
    direct_node = ExecutionNode.objects.filter(assigned_client=client).first()
    if direct_node:
        return direct_node
    broker_node = (
        ClientBrokerdetails.objects.filter(client=client, execution_node__isnull=False)
        .select_related("execution_node")
        .order_by("-id")
        .first()
    )
    return broker_node.execution_node if broker_node else None


def sync_client_broker_execution_nodes(client: User) -> ExecutionNode | None:
    node = get_execution_node_for_client(client)
    if node:
        ClientBrokerdetails.objects.filter(client=client, execution_node__isnull=True).update(execution_node=node)
    return node


def broker_details_has_valid_token(broker_details: ClientBrokerdetails) -> bool:
    if not broker_details:
        return False
    access_token = getattr(broker_details, "access_token", None)
    secure_getter = getattr(broker_details, "get_access_token_secure", None)
    if callable(secure_getter):
        access_token = secure_getter() or access_token
    if not access_token or getattr(broker_details, "isTokenExpired", False):
        return False
    expiry = getattr(broker_details, "access_token_expiry", None)
    if expiry:
        if timezone.is_naive(expiry):
            expiry = timezone.make_aware(expiry)
        if expiry <= timezone.now():
            if not getattr(broker_details, "isTokenExpired", False):
                broker_details.isTokenExpired = True
                broker_details.save(update_fields=["isTokenExpired"])
            return False
    return True


def mark_execution_node_broker_verified_from_valid_token(client: User, node: ExecutionNode) -> bool:
    if not client or not node or not node.is_active:
        return False
    if node.execution_type == ExecutionNode.EXECUTION_TYPE_PROXY and not node.proxy_public_ip_verified:
        return False
    broker_details = (
        ClientBrokerdetails.objects.filter(client=client, execution_node=node)
        .order_by("-tokenCreatedAt", "-id")
        .first()
    )
    if not broker_details or not broker_details_has_valid_token(broker_details):
        return False
    if not node.is_verified_with_broker:
        node.is_verified_with_broker = True
        node.save(update_fields=["is_verified_with_broker", "updated_at"])
        try:
            node.mark_log("broker_verified", "Execution node marked broker verified from an active broker token.", client=client)
        except Exception:
            pass
    return True
