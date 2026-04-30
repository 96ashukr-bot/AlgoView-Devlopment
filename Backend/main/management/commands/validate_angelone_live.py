import json

from django.core.management.base import BaseCommand, CommandError

from main.angelone.services.validation_harness import AngelOneValidationHarness


class Command(BaseCommand):
    help = "Run live/staging validation scenarios for Angel One SmartAPI integration."

    def add_arguments(self, parser):
        parser.add_argument("--broker-details-id", type=int)
        parser.add_argument("--user-email")
        parser.add_argument("--client-code")
        parser.add_argument("--skip-logout", action="store_true")
        parser.add_argument("--skip-concurrency", action="store_true")
        parser.add_argument("--concurrency", type=int, default=5)
        parser.add_argument("--iterations", type=int, default=10)
        parser.add_argument(
            "--inject",
            choices=["redis_down", "broker_down", "network_timeout", "invalid_credentials"],
        )

    def handle(self, *args, **options):
        harness = AngelOneValidationHarness()
        prerequisites = harness.check_prerequisites()
        if prerequisites["status"] != "success":
            self.stdout.write(json.dumps({"status": "error", "stage": "preflight", **prerequisites}, indent=2, default=str))
            raise CommandError(self._build_preflight_error(prerequisites))

        broker_details = harness.resolve_broker_details(
            broker_details_id=options.get("broker_details_id"),
            user_email=options.get("user_email"),
            client_code=options.get("client_code"),
        )
        summary = harness.run_plan(
            broker_details,
            include_logout=not options["skip_logout"],
            run_concurrency=not options["skip_concurrency"],
            concurrency=options["concurrency"],
            iterations=options["iterations"],
            inject=options.get("inject"),
        )
        self.stdout.write(json.dumps(summary, indent=2, default=str))
        if summary["status"] != "success":
            raise CommandError("Angel One validation failed")

    def _build_preflight_error(self, prerequisites):
        first_failure = next((item for item in prerequisites["checks"] if not item["success"]), None)
        if not first_failure:
            return "Validation preflight failed"

        message = first_failure.get("error") or "Validation preflight failed"
        hints = first_failure.get("hints") or []
        if not hints:
            return message
        return f"{message}\nHints:\n- " + "\n- ".join(hints)
