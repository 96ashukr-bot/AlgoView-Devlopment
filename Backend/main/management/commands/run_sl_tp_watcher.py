import time
import json

from django.conf import settings
from django.core.management.base import BaseCommand

from main.sl_tp_watcher_service import get_sl_tp_watcher_service


class Command(BaseCommand):
    help = "Scan open trades and auto-exit them when SL/TP levels are hit."

    def add_arguments(self, parser):
        parser.add_argument("--loop", action="store_true", help="Continuously run the watcher.")
        parser.add_argument(
            "--sleep",
            type=int,
            default=getattr(settings, "SL_TP_WATCHER_SLEEP_SECONDS", 1),
            help="Seconds to wait between scans in loop mode.",
        )
        parser.add_argument("--client-id", type=int, default=None, help="Optional client ID filter.")
        parser.add_argument("--history-id", type=str, default=None, help="Optional history ID filter.")
        parser.add_argument("--dry-run", action="store_true", help="Evaluate SL/TP without sending broker exit orders.")
        parser.add_argument("--json", action="store_true", help="Print the full scan result as JSON.")

    def handle(self, *args, **options):
        service = get_sl_tp_watcher_service()
        loop = options["loop"]
        sleep_seconds = max(int(options["sleep"] or 1), 1)
        client_id = options.get("client_id")
        history_id = options.get("history_id")
        dry_run = options.get("dry_run")
        as_json = options.get("json")

        def run_once():
            scan_result = service.scan(client_id=client_id, history_id=history_id, execute_exit=not dry_run)
            summary = scan_result["summary"]
            if as_json:
                self.stdout.write(json.dumps(scan_result, default=str, indent=2))
                return
            self.stdout.write(
                self.style.SUCCESS(
                    f"SL/TP scan completed: total={summary['total']} triggered={summary['triggered']} "
                    f"monitoring={summary['monitoring']} skipped={summary['skipped']} failed={summary['failed']} "
                    f"target_candidates={summary.get('target_hit_candidates', 0)} "
                    f"stoploss_candidates={summary.get('stoploss_hit_candidates', 0)} "
                    f"price_missing={summary.get('price_missing', 0)} price_stale={summary.get('price_stale', 0)} "
                    f"wrong_contract={summary.get('wrong_contract', 0)} "
                    f"manual_attention={summary.get('manual_attention_required', 0)}"
                )
            )

        if not loop:
            run_once()
            return

        self.stdout.write(self.style.WARNING(f"Starting SL/TP watcher loop. Poll interval: {sleep_seconds}s"))
        while True:
            run_once()
            time.sleep(sleep_seconds)
