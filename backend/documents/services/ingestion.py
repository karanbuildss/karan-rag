import csv
import hashlib
from pathlib import Path

import pymupdf
from budgets.models import FiscalYear
from django.core.files import File
from geography.models import LocalGovernment
from projects.models import Project

from documents.models import ProjectDocumentLink, SourceDocument


class ManifestImportError(ValueError):
    """The evidence manifest is incomplete or points outside its dataset root."""


REQUIRED_COLUMNS = {
    "relative_path",
    "title_en",
    "title_np",
    "document_type",
    "local_government_code",
    "fiscal_year_code",
    "language",
    "source_url",
    "source_url_kind",
    "data_classification",
}


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as source:
        for block in iter(lambda: source.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _resolve_source_file(dataset_root, relative_path):
    candidate = (dataset_root / relative_path).resolve()
    try:
        candidate.relative_to(dataset_root)
    except ValueError as exc:
        raise ManifestImportError("A manifest path escapes the dataset directory.") from exc
    if not candidate.is_file() or candidate.suffix.lower() != ".pdf":
        raise ManifestImportError(f"PDF not found: {relative_path}")
    return candidate


def _cell(row, key):
    return (row.get(key) or "").strip()


def _optional_page(row, key, row_number):
    value = _cell(row, key)
    if not value:
        return None
    try:
        page_number = int(value)
    except ValueError as exc:
        raise ManifestImportError(f"Invalid {key} on manifest row {row_number}.") from exc
    if page_number < 1:
        raise ManifestImportError(f"Invalid {key} on manifest row {row_number}.")
    return page_number


def import_evidence_manifest(manifest_path, *, limit=None):
    manifest_path = Path(manifest_path).resolve()
    if not manifest_path.is_file():
        raise ManifestImportError(f"Manifest not found: {manifest_path}")
    dataset_root = manifest_path.parent.resolve()
    imported = []

    with manifest_path.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        missing_columns = REQUIRED_COLUMNS - set(reader.fieldnames or [])
        if missing_columns:
            raise ManifestImportError(
                f"Manifest is missing columns: {', '.join(sorted(missing_columns))}"
            )

        for row_number, row in enumerate(reader, start=2):
            if limit is not None and len(imported) >= limit:
                break
            try:
                source_file = _resolve_source_file(dataset_root, row["relative_path"])
                local_government = LocalGovernment.objects.get(
                    code=_cell(row, "local_government_code")
                )
                fiscal_year = FiscalYear.objects.get(code=_cell(row, "fiscal_year_code"))
            except (LocalGovernment.DoesNotExist, FiscalYear.DoesNotExist) as exc:
                raise ManifestImportError(
                    f"Unknown geography or fiscal year on manifest row {row_number}."
                ) from exc

            checksum = _sha256(source_file)
            document = SourceDocument.objects.filter(sha256=checksum).first()
            created = document is None
            if created:
                document = SourceDocument(
                    sha256=checksum,
                    original_filename=source_file.name,
                )
            document.title_en = _cell(row, "title_en")
            document.title_np = _cell(row, "title_np")
            document.document_type = _cell(row, "document_type")
            document.local_government = local_government
            document.fiscal_year = fiscal_year
            document.language = _cell(row, "language")
            document.original_filename = source_file.name
            document.source_url = _cell(row, "source_url")
            document.source_url_kind = _cell(row, "source_url_kind")
            document.source_note = _cell(row, "source_note")
            document.data_classification = _cell(row, "data_classification")
            with pymupdf.open(source_file) as pdf:
                document.page_count = len(pdf)
            if created or not document.original_file:
                with source_file.open("rb") as original:
                    document.original_file.save(source_file.name, File(original), save=False)
            document.full_clean()
            document.save()

            project_code = _cell(row, "project_code")
            if project_code:
                try:
                    project = Project.objects.get(code=project_code)
                except Project.DoesNotExist as exc:
                    raise ManifestImportError(
                        f"Unknown project on manifest row {row_number}: {project_code}"
                    ) from exc
                relationship = _cell(row, "relationship")
                if not relationship:
                    raise ManifestImportError(f"Missing relationship on manifest row {row_number}.")
                link, _ = ProjectDocumentLink.objects.update_or_create(
                    project=project,
                    document=document,
                    relationship=relationship,
                    defaults={
                        "page_from": _optional_page(row, "page_from", row_number),
                        "page_to": _optional_page(row, "page_to", row_number),
                        "section": _cell(row, "section"),
                        "evidence_note_en": _cell(row, "evidence_note_en"),
                        "evidence_note_np": _cell(row, "evidence_note_np"),
                    },
                )
                link.full_clean()
                link.save()
            imported.append(document)

    return imported
