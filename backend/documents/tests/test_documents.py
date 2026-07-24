import csv
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

import pymupdf
from budgets.management.commands.seed_demo_data import DEMO_PROJECT_ID
from budgets.models import FiscalYear
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase, override_settings
from django.urls import reverse
from geography.models import LocalGovernment
from PIL import Image
from projects.models import Project
from rest_framework.test import APIClient

from documents.models import DocumentPage, ProjectDocumentLink, SourceDocument
from documents.services import (
    assess_text_quality,
    extract_document,
    extract_document_pages,
    import_evidence_manifest,
)
from documents.services.extraction import _image_from_page


def make_text_pdf(text=""):
    pdf = pymupdf.open()
    page = pdf.new_page()
    if text:
        page.insert_text((72, 72), text, fontsize=10)
    payload = pdf.tobytes()
    pdf.close()
    return payload


def make_multi_page_text_pdf(texts):
    pdf = pymupdf.open()
    for text in texts:
        page = pdf.new_page()
        page.insert_text((72, 72), text, fontsize=10)
    payload = pdf.tobytes()
    pdf.close()
    return payload


class DocumentApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)
        cls.document = SourceDocument.objects.create(
            title_en="Pokhara budget context",
            title_np="पोखरा बजेट सन्दर्भ",
            document_type=SourceDocument.DocumentType.BUDGET_BOOK,
            local_government=LocalGovernment.objects.get(code="PKR"),
            fiscal_year=FiscalYear.objects.get(code="2081-82"),
            language=SourceDocument.Language.NEPALI,
            original_filename="pokhara-budget.pdf",
            sha256="a" * 64,
            source_url="https://pokharamun.gov.np/budget-program",
            source_url_kind=SourceDocument.SourceUrlKind.LANDING_PAGE,
            source_note="Exact attachment URL pending verification.",
            processing_status=SourceDocument.ProcessingStatus.NEEDS_REVIEW,
            page_count=1,
        )
        cls.page = DocumentPage.objects.create(
            document=cls.document,
            page_number=1,
            extracted_text="नगरपालिकाको बजेट विवरण",
            extraction_method=DocumentPage.ExtractionMethod.OCR,
            text_quality_score=Decimal("0.7500"),
            ocr_confidence=Decimal("86.50"),
            review_status=DocumentPage.ReviewStatus.REVIEW_REQUIRED,
            extraction_warnings=["ocr_fallback_used"],
            character_count=24,
        )

    def setUp(self):
        self.client = APIClient()

    def test_document_page_api_preserves_citation_metadata(self):
        response = self.client.get(
            reverse(
                "source-document-page",
                kwargs={"pk": self.document.pk, "page_number": 1},
            )
        )

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["document_id"], str(self.document.id))
        self.assertEqual(data["page_number"], 1)
        self.assertEqual(data["source_url"], self.document.source_url)
        self.assertEqual(data["review_status"], "review_required")

    def test_project_evidence_returns_stable_citation_shape(self):
        ProjectDocumentLink.objects.create(
            project=Project.objects.get(pk=DEMO_PROJECT_ID),
            document=self.document,
            relationship=ProjectDocumentLink.Relationship.CONTEXT,
            page_from=1,
            section="Municipal budget context",
            evidence_note_en="Municipal context for the reconstructed project.",
            evidence_note_np="पुनर्निर्मित आयोजनाको नगर सन्दर्भ।",
        )

        response = self.client.get(reverse("project-evidence", kwargs={"pk": DEMO_PROJECT_ID}))

        self.assertEqual(response.status_code, 200)
        item = response.json()["data"][0]
        self.assertEqual(
            set(item["citation"]),
            {"document_id", "document_title", "page", "section", "source_url"},
        )
        self.assertEqual(item["citation"]["page"], 1)

    def test_database_rejects_duplicate_page_number(self):
        with self.assertRaises(IntegrityError), transaction.atomic():
            DocumentPage.objects.create(
                document=self.document,
                page_number=1,
                extracted_text="duplicate",
            )

    def test_manifest_can_link_a_cited_page_to_the_real_project(self):
        fieldnames = [
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
            "source_note",
            "project_code",
            "relationship",
            "page_from",
            "page_to",
            "section",
            "evidence_note_en",
            "evidence_note_np",
        ]
        with TemporaryDirectory() as dataset_dir, TemporaryDirectory() as media_root:
            dataset_root = Path(dataset_dir)
            (dataset_root / "audit.pdf").write_bytes(make_text_pdf("Official audit evidence"))
            manifest = dataset_root / "manifest.csv"
            with manifest.open("w", encoding="utf-8", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(
                    {
                        "relative_path": "audit.pdf",
                        "title_en": "Linked audit",
                        "title_np": "जोडिएको लेखापरीक्षण",
                        "document_type": "audit_report",
                        "local_government_code": "PKR",
                        "fiscal_year_code": "2077-78",
                        "language": "nep+eng",
                        "source_url": "https://oag.gov.np/reports/local-level-report",
                        "source_url_kind": "landing_page",
                        "data_classification": "official",
                        "project_code": "PKR-W08-JALPA-2077-78",
                        "relationship": "audit",
                        "page_from": "1",
                        "page_to": "1",
                        "section": "Unsettled advance",
                        "evidence_note_en": "Official audit finding for review.",
                    }
                )

            with override_settings(MEDIA_ROOT=media_root):
                documents = import_evidence_manifest(manifest)

            link = ProjectDocumentLink.objects.get(document=documents[0])
            self.assertEqual(link.project_id, DEMO_PROJECT_ID)
            self.assertEqual(link.relationship, ProjectDocumentLink.Relationship.AUDIT)
            self.assertEqual(link.page_from, 1)


class TextQualityTests(TestCase):
    def test_legacy_nepali_font_text_is_sent_to_ocr(self):
        legacy = (
            "jflif{s ljsf; sfo{qmd tyf /ftf] lstfa cf=j= @)&(÷)*) "
            "kf]v/f dxfgu/kflnsf gu/ sfo{kflnsfsf] sfof{no " * 3
        )

        result = assess_text_quality(
            legacy,
            language=SourceDocument.Language.NEPALI,
            min_chars=40,
            min_score=0.62,
        )

        self.assertFalse(result.usable)
        self.assertIn("legacy_nepali_font_suspected", result.warnings)

    def test_clean_english_text_layer_is_accepted(self):
        result = assess_text_quality(
            "This official municipal budget document contains a clear searchable text layer "
            "with enough words to support reliable page-level extraction and review.",
            language=SourceDocument.Language.ENGLISH,
            min_chars=40,
            min_score=0.62,
        )

        self.assertTrue(result.usable)
        self.assertGreaterEqual(result.score, 0.62)

    def test_mixed_nepali_text_with_encoding_artifacts_is_sent_to_ocr(self):
        corrupted = (
            "आधिकारिक लेखापरीक्षण विवरण कÙलकाचोक कृČमा कüČटãéसन जाल्पा मार्ग वडा आठ पेश्की बाँकी विवरण " * 4
        )

        result = assess_text_quality(
            corrupted,
            language=SourceDocument.Language.MIXED,
            min_chars=40,
            min_score=0.62,
        )

        self.assertFalse(result.usable)
        self.assertIn("font_encoding_artifacts_suspected", result.warnings)

    def test_nepali_page_with_partial_legacy_font_header_is_sent_to_ocr(self):
        mixed_legacy = (
            "kf]v/f dxfgu/kflnsf jflif{s ah]6 tyf sfo{qmd cf=j= @)&&÷)&*\n"
            "कार्यक्रम आयोजनाको नाम कार्यान्वयन हुने स्थान विनियोजन रकम " * 5
        )

        result = assess_text_quality(
            mixed_legacy,
            language=SourceDocument.Language.NEPALI,
            min_chars=40,
            min_score=0.62,
        )

        self.assertFalse(result.usable)
        self.assertIn("legacy_nepali_font_suspected", result.warnings)


class DocumentExtractionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)

    def create_document(self, payload, *, language=SourceDocument.Language.ENGLISH):
        return SourceDocument.objects.create(
            title_en="Extraction test document",
            document_type=SourceDocument.DocumentType.OTHER,
            local_government=LocalGovernment.objects.get(code="PKR"),
            fiscal_year=FiscalYear.objects.get(code="2081-82"),
            language=language,
            original_file=SimpleUploadedFile("evidence.pdf", payload, "application/pdf"),
            original_filename="evidence.pdf",
            source_url="https://example.gov.np/evidence.pdf",
            source_url_kind=SourceDocument.SourceUrlKind.DIRECT_PDF,
        )

    def test_uses_clean_embedded_text_without_ocr(self):
        text = (
            "Official municipal budget evidence with a reliable searchable text layer. "
            "The page retains its source, page number, extraction method, and review status."
        )
        with (
            TemporaryDirectory() as media_root,
            override_settings(
                MEDIA_ROOT=media_root,
                OCR_MIN_TEXT_CHARS=40,
                OCR_MIN_QUALITY_SCORE=0.62,
            ),
        ):
            document = self.create_document(make_text_pdf(text))

            with patch("documents.services.extraction._ocr_page") as ocr_page:
                extract_document(document.id)

            ocr_page.assert_not_called()
            page = document.pages.get(page_number=1)
            self.assertEqual(page.extraction_method, DocumentPage.ExtractionMethod.EMBEDDED_TEXT)
            self.assertEqual(page.review_status, DocumentPage.ReviewStatus.AUTO_ACCEPTED)

    def test_unusable_text_layer_uses_ocr_and_requires_review(self):
        with (
            TemporaryDirectory() as media_root,
            override_settings(
                MEDIA_ROOT=media_root,
                OCR_MIN_TEXT_CHARS=40,
                OCR_MIN_QUALITY_SCORE=0.62,
            ),
        ):
            document = self.create_document(make_text_pdf())
            ocr_text = (
                "OCR recovered this official budget page and preserved its page-level source "
                "metadata for a human reviewer."
            )

            with patch(
                "documents.services.extraction._ocr_page",
                return_value=(ocr_text, 91.25),
            ):
                extract_document(document.id)

            document.refresh_from_db()
            page = document.pages.get(page_number=1)
            self.assertEqual(document.processing_status, "needs_review")
            self.assertEqual(page.extraction_method, DocumentPage.ExtractionMethod.OCR)
            self.assertEqual(page.review_status, DocumentPage.ReviewStatus.REVIEW_REQUIRED)
            self.assertEqual(page.ocr_confidence, Decimal("91.25"))

    @override_settings(POPPLER_PATH="C:\\Tools\\poppler\\Library\\bin", OCR_DPI=220)
    def test_poppler_is_a_rendering_fallback(self):
        class BrokenPage:
            def get_pixmap(self, **kwargs):
                raise RuntimeError("primary renderer unavailable")

        rendered = Image.new("RGB", (10, 10), "white")
        with patch(
            "documents.services.extraction.convert_from_path",
            return_value=[rendered],
        ) as convert:
            image = _image_from_page(
                BrokenPage(),
                pdf_path="evidence.pdf",
                page_number=3,
            )

        self.assertEqual(image.mode, "RGB")
        convert.assert_called_once_with(
            "evidence.pdf",
            dpi=220,
            first_page=3,
            last_page=3,
            poppler_path="C:\\Tools\\poppler\\Library\\bin",
            thread_count=1,
        )

    def test_selected_page_extraction_does_not_process_the_whole_pdf(self):
        text = (
            "Official selected evidence page with reliable searchable text and enough "
            "content for the quality gate to accept without OCR."
        )
        payload = make_multi_page_text_pdf([text, text, text])
        with (
            TemporaryDirectory() as media_root,
            override_settings(
                MEDIA_ROOT=media_root,
                OCR_MIN_TEXT_CHARS=40,
                OCR_MIN_QUALITY_SCORE=0.62,
            ),
        ):
            document = self.create_document(payload)

            with patch("documents.services.extraction._ocr_page") as ocr_page:
                pages = extract_document_pages(
                    document.id,
                    [2],
                    sections={2: "Selected evidence"},
                )

            ocr_page.assert_not_called()
            self.assertEqual([page.page_number for page in pages], [2])
            self.assertEqual(document.pages.count(), 1)
            page = document.pages.get()
            self.assertEqual(page.section, "Selected evidence")
            self.assertEqual(page.review_status, DocumentPage.ReviewStatus.AUTO_ACCEPTED)
            record = document.extraction_records.get()
            self.assertEqual(record.details["requested_pages"], [2])
            self.assertTrue(record.details["partial_extraction"])
