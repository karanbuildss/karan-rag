import csv
import hashlib
from decimal import Decimal, InvalidOperation
from pathlib import Path

from config.models import DataClassification
from django.core.exceptions import ValidationError
from django.db import transaction
from documents.models import SourceDocument
from geography.models import LocalGovernment

from budgets.models import BudgetAllocation, FiscalYear, SubSector


class ReviewedBudgetFactImportError(ValueError):
    """A reviewed fact is incomplete, inconsistent, or lacks registered evidence."""


REQUIRED_COLUMNS = {
    "local_government_code",
    "fiscal_year_code",
    "subsector_code",
    "budget_type",
    "allocated_amount",
    "spent_amount",
    "source_relative_path",
    "source_page",
    "review_status",
    "reliability",
    "comparability",
    "source_scope_en",
    "source_scope_np",
    "data_classification",
}


def _cell(row, key):
    return (row.get(key) or "").strip()


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_source_file(dataset_root, relative_path, row_number):
    candidate = (dataset_root / relative_path).resolve()
    try:
        candidate.relative_to(dataset_root)
    except ValueError as exc:
        raise ReviewedBudgetFactImportError(
            f"Source path escapes the dataset directory on row {row_number}."
        ) from exc
    if not candidate.is_file():
        raise ReviewedBudgetFactImportError(
            f"Source evidence is missing on row {row_number}: {relative_path}"
        )
    return candidate


def _decimal(row, key, row_number, *, optional=False):
    value = _cell(row, key)
    if optional and not value:
        return None
    try:
        amount = Decimal(value)
    except InvalidOperation as exc:
        raise ReviewedBudgetFactImportError(
            f"Invalid {key} on reviewed-fact row {row_number}."
        ) from exc
    if amount < 0:
        raise ReviewedBudgetFactImportError(f"Negative {key} on reviewed-fact row {row_number}.")
    return amount


def _choice(row, key, choices, row_number):
    value = _cell(row, key)
    allowed = {choice for choice, _ in choices}
    if value not in allowed:
        raise ReviewedBudgetFactImportError(f"Invalid {key} on reviewed-fact row {row_number}.")
    return value


@transaction.atomic
def import_reviewed_budget_facts(facts_path):
    facts_path = Path(facts_path).resolve()
    if not facts_path.is_file():
        raise ReviewedBudgetFactImportError(f"Reviewed-facts file not found: {facts_path}")
    dataset_root = facts_path.parent.resolve()
    imported = []

    with facts_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            raise ReviewedBudgetFactImportError(
                f"Reviewed-facts file is missing columns: {', '.join(sorted(missing_columns))}"
            )

        for row_number, row in enumerate(reader, start=2):
            source_file = _resolve_source_file(
                dataset_root,
                _cell(row, "source_relative_path"),
                row_number,
            )
            document = SourceDocument.objects.filter(sha256=_sha256(source_file)).first()
            if document is None:
                raise ReviewedBudgetFactImportError(
                    f"Register source evidence before importing reviewed-fact row {row_number}."
                )
            try:
                local_government = LocalGovernment.objects.get(
                    code=_cell(row, "local_government_code")
                )
                fiscal_year = FiscalYear.objects.get(code=_cell(row, "fiscal_year_code"))
                subsector = SubSector.objects.select_related("sector").get(
                    code=_cell(row, "subsector_code")
                )
                source_page = int(_cell(row, "source_page"))
            except (
                LocalGovernment.DoesNotExist,
                FiscalYear.DoesNotExist,
                SubSector.DoesNotExist,
            ) as exc:
                raise ReviewedBudgetFactImportError(
                    f"Unknown geography, fiscal year, or subsector on row {row_number}."
                ) from exc
            except ValueError as exc:
                raise ReviewedBudgetFactImportError(
                    f"Invalid source_page on reviewed-fact row {row_number}."
                ) from exc

            if document.local_government_id != local_government.id:
                raise ReviewedBudgetFactImportError(
                    f"Document municipality mismatch on reviewed-fact row {row_number}."
                )
            if document.fiscal_year_id != fiscal_year.id:
                raise ReviewedBudgetFactImportError(
                    f"Document fiscal-year mismatch on reviewed-fact row {row_number}."
                )
            if source_page < 1 or source_page > document.page_count:
                raise ReviewedBudgetFactImportError(
                    f"Source page is outside the document on reviewed-fact row {row_number}."
                )

            allocation, _ = BudgetAllocation.objects.update_or_create(
                local_government=local_government,
                fiscal_year=fiscal_year,
                subsector=subsector,
                budget_type=_choice(
                    row,
                    "budget_type",
                    BudgetAllocation.BudgetType.choices,
                    row_number,
                ),
                defaults={
                    "allocated_amount": _decimal(row, "allocated_amount", row_number),
                    "spent_amount": _decimal(
                        row,
                        "spent_amount",
                        row_number,
                        optional=True,
                    ),
                    "source_document": document,
                    "source_page": source_page,
                    "review_status": _choice(
                        row,
                        "review_status",
                        BudgetAllocation.ReviewStatus.choices,
                        row_number,
                    ),
                    "reliability": _choice(
                        row,
                        "reliability",
                        BudgetAllocation.Reliability.choices,
                        row_number,
                    ),
                    "comparability": _choice(
                        row,
                        "comparability",
                        BudgetAllocation.Comparability.choices,
                        row_number,
                    ),
                    "source_scope_en": _cell(row, "source_scope_en"),
                    "source_scope_np": _cell(row, "source_scope_np"),
                    "data_classification": _choice(
                        row,
                        "data_classification",
                        DataClassification.choices,
                        row_number,
                    ),
                    "source_url": document.source_url,
                },
            )
            try:
                allocation.full_clean()
            except ValidationError as exc:
                raise ReviewedBudgetFactImportError(
                    f"Reviewed-fact row {row_number} failed model validation."
                ) from exc
            allocation.save()
            imported.append(allocation)

    return imported
