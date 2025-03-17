from django.core.management.base import BaseCommand
from django.utils.timezone import now
from main.models import WebsocketDetails

class Command(BaseCommand):
    help = "Check WebSocket token status and mark expired tokens"

    def handle(self, *args, **kwargs):
        """Check token expiry status and update the database."""
        token = WebsocketDetails.objects.order_by("-id").first()

        if token:
            current_time = now()
            if token.expiry_time and current_time >= token.expiry_time:
                token.token_status = "expired"
                token.save()
                self.stdout.write(self.style.WARNING("Token expired! Status updated."))
            else:
                self.stdout.write(self.style.SUCCESS("Token is still active."))
        else:
            self.stdout.write(self.style.ERROR("No token found in the database."))
