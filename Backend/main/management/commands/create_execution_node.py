from django.core.management.base import BaseCommand, CommandError

from main.models import ExecutionNode


class Command(BaseCommand):
    help = "Create an execution node with encrypted node secret."

    def add_arguments(self, parser):
        parser.add_argument("--name", required=True)
        parser.add_argument("--ip", required=True)
        parser.add_argument("--execution-type", choices=[ExecutionNode.EXECUTION_TYPE_VPS_NODE, ExecutionNode.EXECUTION_TYPE_PROXY], default=ExecutionNode.EXECUTION_TYPE_VPS_NODE)
        parser.add_argument("--server-url", default="")
        parser.add_argument("--provider", default="")
        parser.add_argument("--node-id", default="")
        parser.add_argument("--node-secret", "--secret", dest="node_secret", default="")
        parser.add_argument("--proxy-host", default="")
        parser.add_argument("--proxy-port", type=int)
        parser.add_argument("--proxy-protocol", choices=[ExecutionNode.PROXY_PROTOCOL_HTTP, ExecutionNode.PROXY_PROTOCOL_HTTPS, ExecutionNode.PROXY_PROTOCOL_SOCKS5])
        parser.add_argument("--proxy-username", default="")
        parser.add_argument("--proxy-password", default="")

    def handle(self, *args, **options):
        if ExecutionNode.objects.filter(ip_address=options["ip"]).exists():
            raise CommandError("Execution node IP already exists.")
        node = ExecutionNode(
            name=options["name"],
            ip_address=options["ip"],
            server_url=options["server_url"],
            provider=options["provider"],
            execution_type=options["execution_type"],
            node_id=options["node_id"] or (options["ip"].replace(".", "-") if options["execution_type"] == ExecutionNode.EXECUTION_TYPE_VPS_NODE else None),
            proxy_host=options["proxy_host"] or None,
            proxy_port=options["proxy_port"],
            proxy_protocol=options["proxy_protocol"],
            proxy_username=options["proxy_username"] or None,
        )
        if options["node_secret"]:
            node.set_node_secret(options["node_secret"])
        if options["proxy_password"]:
            node.set_proxy_password(options["proxy_password"])
        node.full_clean()
        node.save()
        self.stdout.write(self.style.SUCCESS(f"Created execution node {node.node_id} ({node.ip_address})"))
