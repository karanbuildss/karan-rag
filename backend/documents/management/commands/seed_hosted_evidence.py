from budgets.services import (
    ReviewedBudgetFactImportError,
    import_reviewed_budget_facts,
)
from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from documents.services import EvidenceCatalogError, import_evidence_catalog


class Command(BaseCommand):
    help = "Seed official source metadata and reviewed facts for a lightweight hosted demo."

    def handle(self, *args, **options):
        try:
            documents = import_evidence_catalog(
                settings.EVIDENCE_MANIFEST,
                facts_path=settings.VERIFIED_BUDGET_FACTS,
            )
            facts = import_reviewed_budget_facts(
                settings.VERIFIED_BUDGET_FACTS,
                catalog_documents=documents,
            )
        except (EvidenceCatalogError, ReviewedBudgetFactImportError) as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Registered {len(documents)} official source records and "
                f"{len(facts)} reviewed facts."
            )
        )
