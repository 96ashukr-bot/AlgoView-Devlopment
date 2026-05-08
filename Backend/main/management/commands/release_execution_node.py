from django.core.management.base import BaseCommand

from main.models import User
from main.services.execution_nodes import release_execution_node


class Command(BaseCommand):
    help = "Release a client's execution node."

    def add_arguments(self, parser):
        parser.add_argument("--client-id", required=True, type=int)

    def handle(self, *args, **options):
        client = User.objects.get(pk=options["client_id"])
        node = release_execution_node(client)
        self.stdout.write(self.style.SUCCESS(f"Released node {node.node_id if node else 'none'} from client {client.id}"))
