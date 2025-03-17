from django.core.management.base import BaseCommand
from django.utils.timezone import now
from main.models import ClientBrokerdetails

class Command(BaseCommand):
    help = "Check broker token expiry and update status"

    def handle(self, *args, **kwargs):
        expired_tokens = ClientBrokerdetails.objects.filter(
            access_token_expiry__lt=now(),
            isTokenExpired=False
        )
        
        updated_count = expired_tokens.update(isTokenExpired=True)

        self.stdout.write(f" Checked tokens: {updated_count} expired tokens updated.")
