import asyncio

from django.core.management.base import BaseCommand

from main.services.upstox_market_data import UpstoxMarketDataCollector, get_active_option_instruments


class Command(BaseCommand):
    help = "Run the Upstox WebSocket market-data collector and cache live option LTPs in Redis."

    def add_arguments(self, parser):
        parser.add_argument("--once", action="store_true", help="Only print the current subscription set.")
        parser.add_argument("--refresh", type=int, default=None, help="Seconds between active trade subscription refreshes.")

    def handle(self, *args, **options):
        if options["once"]:
            instruments = get_active_option_instruments()
            self.stdout.write(self.style.SUCCESS(f"Resolved {len(instruments)} active option instruments."))
            for instrument in instruments[:50]:
                self.stdout.write(f"{instrument.instrument_key} {instrument.trading_symbol}")
            if len(instruments) > 50:
                self.stdout.write(f"... {len(instruments) - 50} more")
            return

        collector = UpstoxMarketDataCollector(refresh_seconds=options.get("refresh"))
        self.stdout.write(self.style.WARNING("Starting Upstox market-data collector."))
        asyncio.run(collector.run_forever())

