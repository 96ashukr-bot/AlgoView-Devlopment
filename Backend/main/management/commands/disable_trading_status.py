from django.core.management.base import BaseCommand
from main.models import ClientTradeSetting

class Command(BaseCommand):
    help = "Disable trading status for all users"

    def handle(self, *args, **kwargs):
        # Set is_tread_status to False for all users
        updated_rows = ClientTradeSetting.objects.update(is_tread_status=False)
        self.stdout.write(f"Trading status disabled for {updated_rows} users.")


