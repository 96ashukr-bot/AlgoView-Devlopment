from django.core.management.base import BaseCommand

from main.services.eod_mis_closure import close_expired_mis_trades


class Command(BaseCommand):
    help = "Mark successful open MIS trades closed after market close using the last/closing price available in the panel."

    def add_arguments(self, parser):
        parser.add_argument("--company-id", type=int, default=None, help="Restrict closure to one white-label company.")
        parser.add_argument("--client-id", action="append", type=int, default=None, help="Restrict closure to one or more clients.")
        parser.add_argument("--trade-id", type=int, default=None, help="Restrict closure to one trade order history row.")
        parser.add_argument("--dry-run", action="store_true", help="Report what would be processed without updating rows.")

    def handle(self, *args, **options):
        result = close_expired_mis_trades(
            company_id=options.get("company_id"),
            client_ids=options.get("client_id"),
            trade_id=options.get("trade_id"),
            dry_run=options.get("dry_run"),
        )
        self.stdout.write(self.style.SUCCESS(f"EOD MIS close completed: {result}"))
