from django.core.management.base import BaseCommand

from main.models import ExecutionNode


class Command(BaseCommand):
    help = "Mark an execution node as broker verified."

    def add_arguments(self, parser):
        parser.add_argument("--node-id", required=True)

    def handle(self, *args, **options):
        node = ExecutionNode.objects.get(node_id=options["node_id"])
        node.is_verified_with_broker = True
        node.save(update_fields=["is_verified_with_broker", "updated_at"])
        node.mark_log("verified", "Execution node marked broker verified from command.")
        self.stdout.write(self.style.SUCCESS(f"Verified node {node.node_id}"))
