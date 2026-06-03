from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from main.legal_services import DEFAULT_AGREEMENT_CONTENT_FILE, seed_agreement_from_file


class Command(BaseCommand):
    help = "Seed the active Software Development and Automation Services Agreement."

    def add_arguments(self, parser):
        parser.add_argument("--content-file", dest="content_file", default=None)
        parser.add_argument("--agreement-version", dest="agreement_version", default="v1.0")

    def handle(self, *args, **options):
        content_file = options["content_file"] or getattr(settings, "MASTER_AGREEMENT_FILE", None) or DEFAULT_AGREEMENT_CONTENT_FILE
        try:
            agreement, created = seed_agreement_from_file(content_file, version=options["agreement_version"])
        except Exception as exc:
            raise CommandError(str(exc)) from exc

        action = "Created" if created else "Activated existing"
        self.stdout.write(
            self.style.SUCCESS(
                f"{action} agreement {agreement.title} {agreement.version} with hash {agreement.content_hash}"
            )
        )
