from django.core.management.base import BaseCommand

from main.models import ExecutionNode, User
from main.services.execution_nodes import assign_execution_node_to_client


class Command(BaseCommand):
    help = "Assign an execution node to a client."

    def add_arguments(self, parser):
        parser.add_argument("--client-id", required=True, type=int)
        parser.add_argument("--node-id", required=True)

    def handle(self, *args, **options):
        client = User.objects.get(pk=options["client_id"])
        node = ExecutionNode.objects.get(node_id=options["node_id"])
        assign_execution_node_to_client(client, node)
        self.stdout.write(self.style.SUCCESS(f"Assigned node {node.node_id} to client {client.id}"))
