from decimal import Decimal
from types import SimpleNamespace

from budgets.management.commands.seed_demo_data import DEMO_PROJECT_ID
from django.core.management import call_command
from django.test import TestCase
from documents.models import DocumentPage, ProjectDocumentLink, SourceDocument
from projects.models import Project

from rag.evidence import (
    materialize_reviewed_page_chunks,
    project_evidence_payloads,
    selected_link_page_numbers,
    split_text,
)


class ReviewedEvidenceChunkTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)
        cls.project = Project.objects.get(pk=DEMO_PROJECT_ID)
        cls.document = SourceDocument.objects.create(
            title_en="Reviewed evidence test",
            document_type=SourceDocument.DocumentType.AUDIT_REPORT,
            local_government=cls.project.local_government,
            fiscal_year=cls.project.fiscal_year,
            language=SourceDocument.Language.MIXED,
            original_filename="reviewed.pdf",
            sha256="f" * 64,
            source_url="https://example.gov.np/reviewed.pdf",
            page_count=2,
        )
        ProjectDocumentLink.objects.create(
            project=cls.project,
            document=cls.document,
            relationship=ProjectDocumentLink.Relationship.AUDIT,
            page_from=1,
            page_to=2,
            section="Audit evidence",
            evidence_note_en="A curator-reviewed, page-linked evidence summary.",
        )
        DocumentPage.objects.create(
            document=cls.document,
            page_number=1,
            extracted_text="Accepted official page text with enough evidence to index.",
            extraction_method=DocumentPage.ExtractionMethod.EMBEDDED_TEXT,
            text_quality_score=Decimal("0.9000"),
            review_status=DocumentPage.ReviewStatus.AUTO_ACCEPTED,
            character_count=58,
        )
        DocumentPage.objects.create(
            document=cls.document,
            page_number=2,
            extracted_text="Unreviewed OCR text must not be indexed.",
            extraction_method=DocumentPage.ExtractionMethod.OCR,
            text_quality_score=Decimal("0.6000"),
            review_status=DocumentPage.ReviewStatus.REVIEW_REQUIRED,
            character_count=40,
        )

    def test_only_accepted_page_text_becomes_document_chunks(self):
        chunks = materialize_reviewed_page_chunks(self.project)

        self.assertEqual(len(chunks), 1)
        self.assertEqual(chunks[0].page.page_number, 1)

    def test_payloads_include_curated_link_and_only_reviewed_page_text(self):
        materialize_reviewed_page_chunks(self.project)

        payloads = project_evidence_payloads(self.project)

        self.assertEqual(len(payloads), 2)
        self.assertEqual(
            {item.metadata["source_kind"] for item in payloads},
            {"curated_project_evidence", "reviewed_document_page"},
        )
        self.assertNotIn("Unreviewed OCR", " ".join(item.text for item in payloads))

    def test_chunks_are_removed_when_a_page_loses_accepted_review_status(self):
        materialize_reviewed_page_chunks(self.project)
        page = self.document.pages.get(page_number=1)
        self.assertEqual(page.chunks.count(), 1)

        page.review_status = DocumentPage.ReviewStatus.REVIEW_REQUIRED
        page.save(update_fields=["review_status", "updated_at"])
        materialize_reviewed_page_chunks(self.project)

        self.assertEqual(page.chunks.count(), 0)

    def test_chunking_is_token_bounded_and_overlapping(self):
        text = " ".join(f"token-{index}" for index in range(45))

        chunks = split_text(text, max_tokens=20, overlap_tokens=5)

        self.assertEqual(len(chunks), 3)
        first = chunks[0].split()
        second = chunks[1].split()
        self.assertEqual(len(first), 20)
        self.assertEqual(first[-5:], second[:5])

    def test_large_linked_ranges_select_boundaries_without_full_pdf_extraction(self):
        link = SimpleNamespace(page_from=1, page_to=30)

        selected = selected_link_page_numbers(link)

        self.assertEqual(selected, [1, 2, 3, 4, 5, 28, 29, 30])
