from django.core.management.base import BaseCommand, CommandError
from projects.models import Project

from rag.evidence import (
    extract_project_linked_pages,
    materialize_reviewed_page_chunks,
    project_evidence_payloads,
)
from rag.providers import VectorStoreUnavailable, get_vector_store_provider


class Command(BaseCommand):
    help = "Index page-linked project evidence using the configured vector provider."

    def add_arguments(self, parser):
        parser.add_argument(
            "--project-code",
            default="PKR-W08-JALPA-2077-78",
            help="Stable project code to index.",
        )
        parser.add_argument(
            "--all-projects",
            action="store_true",
            help="Index every project that has deliberately linked source evidence.",
        )
        parser.add_argument(
            "--extract-linked-pages",
            action="store_true",
            help="Selectively extract cited and high-value boundary pages before indexing.",
        )
        parser.add_argument(
            "--all-linked-pages",
            action="store_true",
            help="Extract every page in each linked range instead of the bounded selection.",
        )
        parser.add_argument(
            "--force-extraction",
            action="store_true",
            help="Re-extract selected pages even when a page record already exists.",
        )

    def handle(self, *args, **options):
        if options["all_projects"]:
            projects = (
                Project.objects.filter(document_links__isnull=False).distinct().order_by("code")
            )
        else:
            try:
                projects = [Project.objects.get(code=options["project_code"])]
            except Project.DoesNotExist as exc:
                raise CommandError("Project not found.") from exc
        if not projects:
            raise CommandError("No projects with linked evidence were found.")
        for project in projects:
            self._index_project(project, options)

    def _index_project(self, project, options):

        extracted_pages = []
        if options["extract_linked_pages"]:
            extracted_pages = extract_project_linked_pages(
                project,
                force=options["force_extraction"],
                include_all=options["all_linked_pages"],
            )
        reviewed_chunks = materialize_reviewed_page_chunks(project)
        payloads = project_evidence_payloads(project)
        if not payloads:
            self.stdout.write(self.style.WARNING(f"Skipped {project.code}: no evidence payloads."))
            return
        try:
            provider = get_vector_store_provider()
            provider.delete_project(str(project.id))
            provider.upsert(payloads)
        except VectorStoreUnavailable as exc:
            raise CommandError(str(exc)) from exc
        except Exception as exc:
            raise CommandError(
                "Evidence indexing failed. Confirm ChromaDB and Ollama are available."
            ) from exc

        self.stdout.write(
            self.style.SUCCESS(
                f"Indexed {len(payloads)} evidence chunks for {project.code} with "
                f"{provider.name}; {len(extracted_pages)} selected pages checked and "
                f"{len(reviewed_chunks)} reviewed page chunks prepared."
            )
        )
        review_required = sorted(
            {
                (page.document.original_filename, page.page_number)
                for page in extracted_pages
                if page.review_status == page.ReviewStatus.REVIEW_REQUIRED
            }
        )
        if review_required:
            formatted = ", ".join(
                f"{filename} p.{page_number}" for filename, page_number in review_required
            )
            self.stdout.write(self.style.WARNING("Not embedded until human approval: " + formatted))
