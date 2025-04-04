from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.db.models import Q
from main.models import ClientBrokerdetails

class Command(BaseCommand):
    help = "Check broker token expiry and update status"

    def handle(self, *args, **kwargs):
        print("time>>",now())
        expired_tokens = ClientBrokerdetails.objects.filter(
            access_token_expiry__lt=now(),
            # isTokenExpired=False
        ).filter(
            Q(broker_name__broker_name__iexact="upstox") |
            Q(broker_name__broker_name__iexact="zerodha") |
            Q(broker_name__broker_name__iexact="5paisa")
        )

        print("expired_tokens >>>>", expired_tokens)

        updated_count = expired_tokens.update(isTokenExpired=True)

        self.stdout.write(f"Checked tokens: {updated_count} expired tokens updated.")
