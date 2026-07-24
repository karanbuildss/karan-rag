from unittest.mock import patch

from budgets.management.commands.seed_demo_data import DEMO_PROJECT_ID
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from documents.models import ProjectDocumentLink, SourceDocument
from projects.models import Project
from rag.providers import VectorStoreUnavailable
from rest_framework.test import APIClient

from investigator.services.generation import GenerationUnavailable


@override_settings(
    INVESTIGATOR_ENABLE_GENERATION=False,
    VECTOR_DB_PROVIDER="database",
    INVESTIGATOR_TOP_K=5,
)
class InvestigatorApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)
        cls.project = Project.objects.get(pk=DEMO_PROJECT_ID)
        evidence_rows = [
            {
                "title": "Pokhara Annual Budget and Program 2077/78",
                "document_type": SourceDocument.DocumentType.BUDGET_BOOK,
                "relationship": ProjectDocumentLink.Relationship.ALLOCATION,
                "page": 168,
                "section": "Gyan Bahadur Jalpa Marg road construction",
                "note": (
                    "The red book records two source rows totalling NPR 800000 for the "
                    "Ward 8 road entry."
                ),
            },
            {
                "title": "Pokhara Jalpa Marg Upgrading Bidding Document 2077/78",
                "document_type": SourceDocument.DocumentType.PROCUREMENT_NOTICE,
                "relationship": ProjectDocumentLink.Relationship.PROCUREMENT,
                "page": 1,
                "section": "Invitation for Bids",
                "note": (
                    "The official tender has Contract ID 45/PMC/NCB/W/077-78 and an "
                    "NPR 9477987.16 estimate; the estimate is not an award or payment."
                ),
            },
            {
                "title": "Pokhara Metropolitan City Audit Report 2077/78",
                "document_type": SourceDocument.DocumentType.AUDIT_REPORT,
                "relationship": ProjectDocumentLink.Relationship.AUDIT,
                "page": 48,
                "section": "Unsettled advance",
                "note": (
                    "The audit names Jalpa Marg drainage and blacktopping and P.L. "
                    "Construction. Two NPR 690000 rows require review before aggregation."
                ),
            },
        ]
        for index, row in enumerate(evidence_rows, start=1):
            document = SourceDocument.objects.create(
                title_en=row["title"],
                title_np="जाल्पा मार्ग स्रोत कागजात",
                document_type=row["document_type"],
                local_government=cls.project.local_government,
                fiscal_year=cls.project.fiscal_year,
                language=SourceDocument.Language.MIXED,
                original_filename=f"evidence-{index}.pdf",
                sha256=str(index) * 64,
                source_url=f"https://example.gov.np/evidence-{index}.pdf",
                processing_status=SourceDocument.ProcessingStatus.APPROVED,
                page_count=max(row["page"], 1),
            )
            ProjectDocumentLink.objects.create(
                project=cls.project,
                document=document,
                relationship=row["relationship"],
                page_from=row["page"],
                page_to=row["page"],
                section=row["section"],
                evidence_note_en=row["note"],
                evidence_note_np="आधिकारिक स्रोतको पृष्ठगत प्रमाण।",
            )

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("investigator-query")

    def ask(self, question, **extra):
        return self.client.post(
            self.url,
            {"question": question, "project_id": str(self.project.id), **extra},
            format="json",
        )

    def test_romanized_money_journey_combines_database_and_citations(self):
        response = self.ask("Pokhara Ward 8 ko road project ko paisa kaha gayo?")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["route"], "PROJECT_INVESTIGATION")
        self.assertEqual(data["language"], "romanized_ne")
        self.assertIn("NPR 800,000.00", data["answer"])
        self.assertIn("NPR 9,477,987.16", data["answer"])
        self.assertIn("payment amount hoina", data["answer"])
        self.assertEqual(data["structured_facts"]["budget"]["allocated_amount"], "800000.00")
        self.assertIsNone(data["structured_facts"]["payments"]["reported_total"])
        self.assertEqual(len(data["citations"]), 3)
        self.assertEqual(
            {item["page"] for item in data["citations"]},
            {1, 48, 168},
        )

    def test_payment_question_uses_database_and_preserves_unknown(self):
        response = self.ask("How much was paid?")

        data = response.json()["data"]
        self.assertEqual(data["route"], "DATABASE_QUERY")
        self.assertIn("unknown, not zero spending", data["answer"])
        self.assertEqual(data["provenance"]["structured_values"], "relational_database")
        self.assertIn("payments", data["structured_facts"]["unknown_fields"])

    def test_audit_question_returns_page_specific_evidence(self):
        response = self.ask("What does the audit report say?")

        data = response.json()["data"]
        self.assertEqual(data["route"], "DOCUMENT_RAG")
        self.assertIn("Two NPR 690000 rows require review", data["answer"])
        self.assertEqual(data["citations"][0]["relationship"], "audit")
        self.assertEqual(data["citations"][0]["page"], 48)

    def test_missing_project_context_returns_insufficient_evidence(self):
        response = self.client.post(
            self.url,
            {"question": "Where did the project money go?"},
            format="json",
        )

        data = response.json()["data"]
        self.assertEqual(data["route"], "INSUFFICIENT_EVIDENCE")
        self.assertIsNone(data["project"])
        self.assertIn("enough evidence", data["answer"])

    @override_settings(INVESTIGATOR_ENABLE_GENERATION=True)
    @patch(
        "investigator.services.investigation.refine_with_ollama",
        side_effect=GenerationUnavailable("offline"),
    )
    def test_ollama_failure_returns_safe_deterministic_answer(self, refine):
        response = self.ask("Where did the money go?")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["provenance"]["answer_generation"], "deterministic_fallback")
        self.assertIn("not a contract award or payment", data["answer"])
        refine.assert_called_once()

    @override_settings(VECTOR_DB_PROVIDER="chroma")
    @patch(
        "investigator.services.retrieval.get_vector_store_provider",
        side_effect=VectorStoreUnavailable("offline"),
    )
    def test_vector_failure_falls_back_to_database_evidence(self, provider):
        response = self.ask("What does the tender document say?")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["provenance"]["document_retrieval"], "bm25_evidence")
        self.assertTrue(data["citations"])
        provider.assert_called_once()

    def test_short_question_returns_stable_validation_error(self):
        response = self.client.post(self.url, {"question": "?"}, format="json")

        self.assertEqual(response.status_code, 400)
        error = response.json()["errors"][0]
        self.assertEqual(error["code"], "question_too_short")
        self.assertEqual(error["field"], "question")
