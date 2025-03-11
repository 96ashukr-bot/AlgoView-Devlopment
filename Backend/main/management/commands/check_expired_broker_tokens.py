from django.core.management.base import BaseCommand
from django.utils.timezone import now
from main.models import ClientBrokerdetails

class Command(BaseCommand):
    help = 'Check and update expired tokens'

    def handle(self, *args, **kwargs):
        expired_brokers = ClientBrokerdetails.objects.filter(access_token_expiry__lt=now())

        for broker in expired_brokers:
            broker.isTokenExpired = True
            broker.save()
            self.stdout.write(self.style.SUCCESS(f'Token expired for user: {broker.client}'))

        self.stdout.write(self.style.SUCCESS('Token expiration check completed.'))
