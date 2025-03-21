from django.core.management.base import BaseCommand
from django.utils.timezone import now
from main.models import User

class Command(BaseCommand):
    help = 'Update the status of expired and non-expired clients'

    def handle(self, *args, **kwargs):
        current_date = now().date()
        self.stdout.write(f"Current Date: {current_date}")

        try:
            # Update expired clients
            expired_clients = User.objects.filter(
                end_date_client__lte=current_date,
                type_of_user='is_client',
                is_client=True
            )
            expired_count = expired_clients.update(client_expiry_status=True)
            self.stdout.write(f"Updated {expired_count} expired client(s) to expired status.")

            # Update non-expired clients
            non_expired_clients = User.objects.filter(
                end_date_client__gte=current_date,
                type_of_user='is_client',
                is_client=True
            )
            non_expired_count = non_expired_clients.update(client_expiry_status=False)
            self.stdout.write(f"Updated {non_expired_count} non-expired client(s) to active status.")

        except Exception as e:
            self.stderr.write(f"Error: {str(e)}")
