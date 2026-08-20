import time
from urllib.parse import urljoin

import requests
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from main.services.node_security import generate_node_signature


class Command(BaseCommand):
    help = "Send signed heartbeats from an AWS VPS execution node to the main AlgoView server."

    def add_arguments(self, parser):
        parser.add_argument("--interval", type=int, default=30)
        parser.add_argument("--once", action="store_true")

    def _send(self):
        if not settings.ALGOVIEW_NODE_MODE:
            raise CommandError("ALGOVIEW_NODE_MODE must be enabled.")
        if not settings.ALGOVIEW_NODE_ID or not settings.ALGOVIEW_NODE_SECRET:
            raise CommandError("ALGOVIEW_NODE_ID and ALGOVIEW_NODE_SECRET are required.")
        if not settings.ALGOVIEW_MAIN_SERVER_URL:
            raise CommandError("ALGOVIEW_MAIN_SERVER_URL is required.")

        public_ip = requests.get("https://api.ipify.org", timeout=5).text.strip()
        payload = {"node_id": settings.ALGOVIEW_NODE_ID, "public_ip": public_ip}
        timestamp = str(int(time.time()))
        headers = {
            "X-ALGOVIEW-NODE-ID": settings.ALGOVIEW_NODE_ID,
            "X-ALGOVIEW-TIMESTAMP": timestamp,
            "X-ALGOVIEW-SIGNATURE": generate_node_signature(settings.ALGOVIEW_NODE_SECRET, timestamp, payload),
        }
        url = urljoin(settings.ALGOVIEW_MAIN_SERVER_URL.rstrip("/") + "/", "api/node/heartbeat/")
        response = requests.post(url, json=payload, headers=headers, timeout=settings.NODE_REQUEST_TIMEOUT)
        response.raise_for_status()
        self.stdout.write(self.style.SUCCESS(f"Heartbeat accepted for {settings.ALGOVIEW_NODE_ID} from {public_ip}."))

    def handle(self, *args, **options):
        interval = max(10, int(options["interval"]))
        while True:
            try:
                self._send()
            except (requests.RequestException, CommandError) as exc:
                self.stderr.write(self.style.ERROR(str(exc)))
                if isinstance(exc, CommandError):
                    raise
            if options["once"]:
                return
            time.sleep(interval)
