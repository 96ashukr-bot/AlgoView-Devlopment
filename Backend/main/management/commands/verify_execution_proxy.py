from django.core.management.base import BaseCommand

from main.models import ExecutionNode
from main.services.proxy_utils import verify_proxy_public_ip


class Command(BaseCommand):
    help = "Verify an execution proxy's outgoing public IP."

    def add_arguments(self, parser):
        parser.add_argument("--node-id", required=True)

    def handle(self, *args, **options):
        node = ExecutionNode.objects.get(node_id=options["node_id"])
        result = verify_proxy_public_ip(node)
        self.stdout.write(f"Expected IP: {result.get('expected_ip')}")
        self.stdout.write(f"Actual IP: {result.get('actual_ip')}")
        self.stdout.write(str(result))
