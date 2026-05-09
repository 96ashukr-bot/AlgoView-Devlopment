from __future__ import annotations

from django.core.exceptions import ValidationError
from django.db import transaction

from main.models import ClientBrokerdetails, ExecutionNode, User


def verify_node_available(node: ExecutionNode) -> None:
    if not node:
        raise ValidationError("Execution node is required.")
    if not node.is_active or node.status == ExecutionNode.STATUS_DISABLED:
        raise ValidationError("Execution node is not active.")
    if node.status == ExecutionNode.STATUS_MAINTENANCE:
        raise ValidationError("Execution node is in maintenance mode.")
    if node.assigned_client_id:
        raise ValidationError("Execution node is already assigned to another client.")
    if node.execution_type == ExecutionNode.EXECUTION_TYPE_PROXY:
        if not (node.proxy_host and node.proxy_port and node.proxy_protocol):
            raise ValidationError("Proxy execution node is missing proxy host, port, or protocol.")


@transaction.atomic
def assign_execution_node_to_client(client: User, node: ExecutionNode) -> ExecutionNode:
    client = User.objects.select_for_update().get(pk=client.pk)
    node = ExecutionNode.objects.select_for_update().get(pk=node.pk)
    if ExecutionNode.objects.filter(assigned_client=client).exclude(pk=node.pk).exists():
        raise ValidationError("Client already has an execution node.")
    if node.assigned_client_id and node.assigned_client_id != client.id:
        raise ValidationError("Execution node is already assigned to another client.")
    if not node.is_active:
        raise ValidationError("Inactive execution node cannot be assigned.")
    if node.execution_type == ExecutionNode.EXECUTION_TYPE_PROXY and not (node.proxy_host and node.proxy_port and node.proxy_protocol):
        raise ValidationError("Proxy execution node is missing proxy host, port, or protocol.")

    node.assigned_client = client
    node.status = ExecutionNode.STATUS_ASSIGNED
    node.save(update_fields=["assigned_client", "status", "updated_at"])
    ClientBrokerdetails.objects.filter(client=client).update(execution_node=node)
    node.mark_log("assigned", "Execution node assigned to client.", client=client)
    return node


@transaction.atomic
def release_execution_node(client: User) -> ExecutionNode | None:
    node = ExecutionNode.objects.select_for_update().filter(assigned_client=client).first()
    if not node:
        ClientBrokerdetails.objects.filter(client=client).update(execution_node=None)
        return None
    node.assigned_client = None
    node.status = ExecutionNode.STATUS_FREE if node.is_active else ExecutionNode.STATUS_DISABLED
    node.save(update_fields=["assigned_client", "status", "updated_at"])
    ClientBrokerdetails.objects.filter(client=client, execution_node=node).update(execution_node=None)
    node.mark_log("released", "Execution node released from client.", client=client)
    return node


def get_execution_node_for_client(client: User) -> ExecutionNode | None:
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
