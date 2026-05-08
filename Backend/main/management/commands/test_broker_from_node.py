from django.core.management.base import BaseCommand

from main.brokers import get_broker_adapter
from main.models import ClientBrokerdetails, User


class Command(BaseCommand):
    help = "Validate broker adapter credentials for a client as the node would see them."

    def add_arguments(self, parser):
        parser.add_argument("--client-id", required=True, type=int)

    def handle(self, *args, **options):
        client = User.objects.get(pk=options["client_id"])
        broker_details = ClientBrokerdetails.objects.filter(client=client).select_related("broker_name").order_by("-id").first()
        if not broker_details:
            self.stderr.write("No broker details found.")
            return
        adapter = get_broker_adapter(broker_details)
        self.stdout.write(str(adapter.validate_credentials()))
