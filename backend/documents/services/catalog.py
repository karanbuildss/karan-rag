import csv
from pathlib import Path
from uuid import NAMESPACE_URL, uuid5

from budgets.models import FiscalYear
from django.db import transaction
from geography.models import LocalGovernment
from projects.models import Project

from documents.models import ProjectDocumentLink, SourceDocument


class EvidenceCatalogError(ValueError):
    """The hosted evidence catalogue cannot be built from committed metadata."""


def _cell(row, key):
    return (row.get(key) or "").strip()


def _catalog_id(relative_path):
    return uuid5(NAMESPACE_URL, f"budget-darpan:official-source:{relative_path.casefold()}")


def _known_page_counts(manifest_path, facts_path):
    counts = {}
    if facts_path and Path(facts_path).is_file():
        with Path(facts_path).open("r", encoding="utf-8-sig", newline="") as source:
            for row in csv.DictReader(source):
                relative_path = _cell(row, "source_relative_path")
                try:
                    page = int(_cell(row, "source_page") or 0)
                except ValueError:
                    page = 0
                counts[relative_path] = max(counts.get(relative_path, 0), page)

    with Path(manifest_path).open("r", encoding="utf-8-sig", newline="") as source:
        for row in csv.DictReader(source):
            relative_path = _cell(row, "relative_path")
            for key in ("page_from", "page_to"):
                try:
                    page = int(_cell(row, key) or 0)
                except ValueError:
                    page = 0
                counts[relative_path] = max(counts.get(relative_path, 0), page)
    return counts


@transaction.atomic
def import_evidence_catalog(manifest_path, *, facts_path=None):
    """Register official source metadata even when large originals are not deployed.

    The local ingestion command remains responsible for hashing, preserving, extracting,
    and reviewing original files. This catalogue gives hosted users the real official URL,
    provenance, and cited page without pretending that the cloud has the original PDF.
    """

    manifest_path = Path(manifest_path).resolve()
    if not manifest_path.is_file():
        raise EvidenceCatalogError(f"Evidence manifest not found: {manifest_path}")
    page_counts = _known_page_counts(manifest_path, facts_path)
    documents = {}

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        for row_number, row in enumerate(reader, start=2):
            relative_path = _cell(row, "relative_path")
            if not relative_path:
                raise EvidenceCatalogError(f"Missing relative_path on manifest row {row_number}.")
            try:
                local_government = LocalGovernment.objects.get(
                    code=_cell(row, "local_government_code")
                )
                fiscal_year = FiscalYear.objects.get(code=_cell(row, "fiscal_year_code"))
            except (LocalGovernment.DoesNotExist, FiscalYear.DoesNotExist) as exc:
                raise EvidenceCatalogError(
                    f"Unknown geography or fiscal year on manifest row {row_number}."
                ) from exc

            document = documents.get(relative_path)
            if document is None:
                filename = Path(relative_path).name
                document = (
                    SourceDocument.objects.filter(
                        local_government=local_government,
                        fiscal_year=fiscal_year,
                        original_filename=filename,
                    )
                    .order_by("-updated_at")
                    .first()
                )
                if document is None:
                    document = SourceDocument(id=_catalog_id(relative_path))

                source_note = _cell(row, "source_note")
                hosted_note = (
                    "Official source metadata is available in the hosted demo. The preserved "
                    "original and extracted pages remain in the local research corpus."
                )
                document.title_en = _cell(row, "title_en")
                document.title_np = _cell(row, "title_np")
                document.document_type = _cell(row, "document_type")
                document.local_government = local_government
                document.fiscal_year = fiscal_year
                document.language = _cell(row, "language")
                document.file_format = (
                    SourceDocument.FileFormat.IMAGE
                    if Path(relative_path).suffix.casefold() in {".png", ".jpg", ".jpeg"}
                    else SourceDocument.FileFormat.PDF
                )
                document.original_filename = filename
                document.source_url = _cell(row, "source_url")
                document.source_url_kind = _cell(row, "source_url_kind")
                document.source_note = f"{source_note} {hosted_note}".strip()
                document.data_classification = _cell(row, "data_classification")
                document.page_count = max(
                    document.page_count,
                    page_counts.get(relative_path, 0),
                )
                if not document.original_file and not document.pages.exists():
                    document.processing_status = SourceDocument.ProcessingStatus.PENDING
                document.full_clean()
                document.save()
                documents[relative_path] = document

            project_code = _cell(row, "project_code")
            relationship = _cell(row, "relationship")
            if project_code and relationship:
                try:
                    project = Project.objects.get(code=project_code)
                except Project.DoesNotExist as exc:
                    raise EvidenceCatalogError(
                        f"Unknown project on manifest row {row_number}: {project_code}"
                    ) from exc

                page_from_value = _cell(row, "page_from")
                page_to_value = _cell(row, "page_to")

                link, _ = ProjectDocumentLink.objects.update_or_create(
                    project=project,
                    document=document,
                    relationship=relationship,
                    defaults={
                        "page_from": int(page_from_value) if page_from_value else None,
                        "page_to": int(page_to_value) if page_to_value else None,
                        "section": _cell(row, "section"),
                        "evidence_note_en": _cell(row, "evidence_note_en"),
                        "evidence_note_np": _cell(row, "evidence_note_np"),
                    },
                )
                link.full_clean()
                link.save()

    return documents
