from django.core.management.base import BaseCommand, CommandError

from main.brokers import get_broker_adapter
from main.models import ClientBrokerdetails, ExecutionNode, User
from main.services.execution_nodes import get_execution_node_for_client
from main.services.proxy_utils import build_requests_proxy_config


class Command(BaseCommand):
    help = "Fetch orderbook through a client's assigned proxy route."

    def add_arguments(self, parser):
        parser.add_argument("--client-id", required=True, type=int)

    def handle(self, *args, **options):
        client = User.objects.get(pk=options["client_id"])
        node = get_execution_node_for_client(client)
        if not node or node.execution_type != ExecutionNode.EXECUTION_TYPE_PROXY:
            raise CommandError("Client does not have a proxy execution node.")
        broker_details = ClientBrokerdetails.objects.filter(client=client).select_related("broker_name").order_by("-id").first()
        if not broker_details:
            raise CommandError("No broker details found.")
        adapter = get_broker_adapter(broker_details)
        if not adapter.supports_proxy:
            raise CommandError("This broker adapter does not currently support proxy-based execution.")
        self.stdout.write(str(adapter.get_orderbook(proxy_config=build_requests_proxy_config(node))))
