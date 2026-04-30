import json

from django.core.management.base import BaseCommand, CommandError

from main.angelone.services.validation_harness import AngelOneValidationHarness


class Command(BaseCommand):
    help = "Check local infrastructure dependencies required for Angel One live validation."

    def add_arguments(self, parser):
        parser.add_argument("--broker-details-id", type=int)
        parser.add_argument("--user-email")
        parser.add_argument("--client-code")

    def handle(self, *args, **options):
        harness = AngelOneValidationHarness()
        report = harness.check_prerequisites()

        selector = {
            "broker_details_id": options.get("broker_details_id"),
            "user_email": options.get("user_email"),
            "client_code": options.get("client_code"),
        }

        if any(selector.values()):
            broker_details = harness.resolve_broker_details(**selector)
            report["broker_details"] = {
                "id": broker_details.id,
                "client_code": broker_details.get_canonical_client_code(),
                "has_api_key": bool(broker_details.broker_API_KEY),
                "has_password": bool(broker_details.get_broker_password()),
                "has_totp_secret": bool(broker_details.get_broker_totp_secret()),
            }

        self.stdout.write(json.dumps(report, indent=2, default=str))
        if report["status"] != "success":
            raise CommandError(self._build_failure_message(report))

    def _build_failure_message(self, report):
        failure = next((item for item in report["checks"] if not item["success"]), None)
        if not failure:
            return "Angel One dependency check failed"

        message = failure.get("error") or "Angel One dependency check failed"
        hints = failure.get("hints") or []
        if not hints:
            return message
        return f"{message}\nHints:\n- " + "\n- ".join(hints)
