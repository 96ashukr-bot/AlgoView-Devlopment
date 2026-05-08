from django.core.management.base import BaseCommand, CommandError

from main.models import ExecutionNode


class Command(BaseCommand):
    help = "Create an execution node with encrypted node secret."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True)
        parser.add_argument("--ip", required=True)
        parser.add_argument("--server-url", required=True)
        parser.add_argument("--provider", default="")
        parser.add_argument("--node-id", default="")
        parser.add_argument("--secret", default="")

    def handle(self, *args, **options):
        if ExecutionNode.objects.filter(ip_address=options["ip"]).exists():
            raise CommandError("Execution node IP already exists.")
        node = ExecutionNode(
            name=options["name"],
            ip_address=options["ip"],
            server_url=options["server_url"],
            provider=options["provider"],
            node_id=options["node_id"] or options["ip"].replace(".", "-"),
        )
        if options["secret"]:
            node.set_node_secret(options["secret"])
        node.save()
        self.stdout.write(self.style.SUCCESS(f"Created execution node {node.node_id} ({node.ip_address})"))
