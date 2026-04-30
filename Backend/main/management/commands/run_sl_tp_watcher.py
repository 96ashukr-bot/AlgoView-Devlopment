import time

from django.core.management.base import BaseCommand

from main.sl_tp_watcher_service import get_sl_tp_watcher_service


class Command(BaseCommand):
    help = "Scan open trades and auto-exit them when SL/TP levels are hit."

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true", help="Continuously run the watcher.")
        parser.add_argument("--sleep", type=int, default=5, help="Seconds to wait between scans in loop mode.")
        parser.add_argument("--client-id", type=int, default=None, help="Optional client ID filter.")
        parser.add_argument("--history-id", type=str, default=None, help="Optional history ID filter.")

    def handle(self, *args, **options):
        service = get_sl_tp_watcher_service()
        loop = options["loop"]
        sleep_seconds = max(int(options["sleep"] or 1), 1)
        client_id = options.get("client_id")
        history_id = options.get("history_id")

        def run_once():
            scan_result = service.scan(client_id=client_id, history_id=history_id)
            summary = scan_result["summary"]
            self.stdout.write(
                self.style.SUCCESS(
                    f"SL/TP scan completed: total={summary['total']} triggered={summary['triggered']} "
                    f"monitoring={summary['monitoring']} skipped={summary['skipped']} failed={summary['failed']}"
                )
            )

        if not loop:
            run_once()
            return

        self.stdout.write(self.style.WARNING(f"Starting SL/TP watcher loop. Poll interval: {sleep_seconds}s"))
        while True:
            run_once()
            time.sleep(sleep_seconds)
