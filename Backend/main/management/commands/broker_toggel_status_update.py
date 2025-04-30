from django.core.management.base import BaseCommand
from main.models import User

class Command(BaseCommand):
    help = "Disable trading status for all users"

    def handle(self, *args, **kwargs):
        # Set is_tread_status to False for all users
        updated_rows = User.objects.update(is_enable=False)
        self.stdout.write(f"broker toggel is_enable status is disabled for {updated_rows} users.")