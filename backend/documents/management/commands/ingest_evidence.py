from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from documents.services import (
    DocumentExtractionError,
    ManifestImportError,
    extract_document,
    import_evidence_manifest,
)


class Command(BaseCommand):
    help = "Register the evidence manifest and optionally extract each PDF page-by-page."

    def add_arguments(self, parser):
        parser.add_argument("--manifest", default=str(settings.EVIDENCE_MANIFEST))
        parser.add_argument("--limit", type=int)
        parser.add_argument(
            "--filename",
            help="Extract only the registered document with this original filename.",
        )
        parser.add_argument(
            "--extract",
            action="store_true",
            help="Run direct extraction and selective OCR after registration.",
        )
        parser.add_argument(
            "--max-pages",
            type=int,
            help="Process only the first N pages per file for a smoke test.",
        )
        parser.add_argument("--force", action="store_true")

    def handle(self, *args, **options):
        try:
            documents = import_evidence_manifest(options["manifest"], limit=options["limit"])
        except ManifestImportError as exc:
            raise CommandError(str(exc)) from exc

        self.stdout.write(self.style.SUCCESS(f"Registered {len(documents)} source documents."))
        if not options["extract"]:
            self.stdout.write("Extraction was not requested; originals remain pending.")
            return

        if options["filename"]:
            documents = [
                document
                for document in documents
                if document.original_filename == options["filename"]
            ]
            if not documents:
                raise CommandError(f"No registered document has filename: {options['filename']}")

        failures = 0
        for document in documents:
            self.stdout.write(f"Extracting {document.original_filename}...")
            try:
                extract_document(
                    document.id,
                    force=options["force"],
                    max_pages=options["max_pages"],
                )
            except DocumentExtractionError as exc:
                failures += 1
                self.stderr.write(self.style.ERROR(f"{document.original_filename}: {exc}"))

        if failures:
            raise CommandError(f"{failures} document(s) could not be extracted.")
        self.stdout.write(self.style.SUCCESS("Evidence extraction completed."))
