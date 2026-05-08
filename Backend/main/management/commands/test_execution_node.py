import requests
from django.conf import settings
from django.core.management.base import BaseCommand

from main.models import ExecutionNode


class Command(BaseCommand):
    help = "Call an execution node health endpoint."

    def add_arguments(self, parser):
        parser.add_argument("--node-id", required=True)

    def handle(self, *args, **options):
        node = ExecutionNode.objects.get(node_id=options["node_id"])
        response = requests.get(node.server_url.rstrip("/") + "/api/node/health/", timeout=settings.NODE_REQUEST_TIMEOUT)
        self.stdout.write(f"HTTP {response.status_code}: {response.text[:1000]}")
