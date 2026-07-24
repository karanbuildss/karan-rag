from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from budgets.services import ReviewedBudgetFactImportError, import_reviewed_budget_facts


class Command(BaseCommand):
    help = "Import human-reviewed structured budget facts with document/page provenance."

    def add_arguments(self, parser):
        parser.add_argument("--facts", default=str(settings.VERIFIED_BUDGET_FACTS))

    def handle(self, *args, **options):
        try:
            allocations = import_reviewed_budget_facts(options["facts"])
        except ReviewedBudgetFactImportError as exc:
            raise CommandError(str(exc)) from exc
        self.stdout.write(self.style.SUCCESS(f"Imported {len(allocations)} reviewed budget facts."))
