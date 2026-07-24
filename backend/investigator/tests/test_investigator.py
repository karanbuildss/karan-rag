from unittest.mock import patch

from anomalies.services import evaluate_project
from budgets.management.commands.seed_demo_data import DEMO_PROJECT_ID
from budgets.services.showcase import SHOWCASE_PROJECT_ID
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from documents.models import DocumentPage, ProjectDocumentLink, SourceDocument
from projects.models import Project
from rag.evidence import materialize_reviewed_page_chunks
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

    def test_flag_question_uses_explainable_deterministic_anomalies(self):
        evaluate_project(self.project)

        response = self.ask("Why is this project flagged?")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["route"], "ANOMALY_EXPLANATION")
        self.assertEqual(data["provenance"]["anomaly_analysis"], "deterministic_rules")
        self.assertEqual(
            data["provenance"]["document_retrieval"],
            "deterministic_anomaly_sources",
        )
        self.assertTrue(data["anomalies"])
        self.assertTrue(data["citations"])
        self.assertIn("review signals", data["answer"])
        self.assertNotIn("fraud", data["answer"].casefold())
        self.assertNotIn("corruption", data["answer"].casefold())
        self.assertTrue(data["anomalies"][0]["threshold"])

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


@override_settings(
    INVESTIGATOR_ENABLE_GENERATION=False,
    VECTOR_DB_PROVIDER="database",
    INVESTIGATOR_TOP_K=5,
)
class RupaEventInvestigatorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)
        cls.project = Project.objects.get(code="RUPA-W02-ANDHERI-CULVERT-2080-81")
        document = SourceDocument.objects.create(
            title_en="Rupa Rural Municipality Annual Progress Report 2080/81",
            title_np="रूपा गाउँपालिका वार्षिक प्रगति प्रतिवेदन २०८०/८१",
            document_type=SourceDocument.DocumentType.PROGRESS_REPORT,
            local_government=cls.project.local_government,
            fiscal_year=cls.project.fiscal_year,
            language=SourceDocument.Language.NEPALI,
            original_filename="rupa-progress.pdf",
            sha256="9" * 64,
            source_url="https://rupamun.gov.np/annual-progress-report",
            processing_status=SourceDocument.ProcessingStatus.APPROVED,
            page_count=71,
        )
        ProjectDocumentLink.objects.create(
            project=cls.project,
            document=document,
            relationship=ProjectDocumentLink.Relationship.PROGRESS,
            page_from=51,
            page_to=51,
            section="Ward 2 project implementation status",
            evidence_note_en=(
                "The official row reports NPR 200000 allocated, agreement 2080/12/28, "
                "monitoring 2081/02/02, and payment date 2081/02/03. The paid amount "
                "and completion percentage are not published."
            ),
            evidence_note_np=(
                "आधिकारिक पङ्क्तिमा रु. २००००० विनियोजन, सम्झौता २०८०/१२/२८, "
                "अनुगमन २०८१/०२/०२ र भुक्तानी मिति २०८१/०२/०३ उल्लेख छन्।"
            ),
        )
        page_text = (
            "Ward 2 project implementation status. Andheri Khola Culvert Construction, "
            "Rupa-2. Allocated NPR 200000. Agreement 2080/12/28. Monitoring "
            "2081/02/02. Payment date 2081/02/03. The table has no paid amount or "
            "completion percentage."
        )
        DocumentPage.objects.create(
            document=document,
            page_number=51,
            section="Ward 2 project implementation status",
            extracted_text=page_text,
            extraction_method=DocumentPage.ExtractionMethod.EMBEDDED_TEXT,
            text_quality_score="0.9800",
            review_status=DocumentPage.ReviewStatus.APPROVED,
            character_count=len(page_text),
        )
        materialize_reviewed_page_chunks(cls.project)

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("investigator-query")

    def ask(self, question):
        return self.client.post(
            self.url,
            {"question": question, "project_id": str(self.project.id)},
            format="json",
        )

    def test_romanized_money_journey_combines_events_rag_and_unknown_amount(self):
        response = self.ask("Rupa-2 ko culvert ko paisa kaha gayo?")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["route"], "PROJECT_INVESTIGATION")
        self.assertEqual(data["language"], "romanized_ne")
        self.assertIn("NPR 200,000.00", data["answer"])
        self.assertIn("agreement 2080/12/28", data["answer"])
        self.assertIn("payment date 2081/02/03", data["answer"])
        self.assertIn("actual paid amount publish bhayeko chaina", data["answer"])
        self.assertIn("page 51", data["answer"])
        self.assertEqual(
            data["structured_facts"]["payments"]["status"],
            "date_reported_amount_missing",
        )
        self.assertEqual(len(data["structured_facts"]["evidence_events"]), 3)
        self.assertTrue(
            any(
                citation["page"] == 51 and citation["source_kind"] == "reviewed_document_page"
                for citation in data["citations"]
            )
        )

    def test_nepali_payment_question_reports_date_without_inventing_amount(self):
        response = self.ask("भुक्तानी मिति र रकम कति हो?")

        data = response.json()["data"]
        self.assertEqual(data["route"], "DATABASE_QUERY")
        self.assertEqual(data["language"], "ne")
        self.assertIn("2081/02/03", data["answer"])
        self.assertIn("भुक्तानी रकम प्रकाशित छैन", data["answer"])
        self.assertIn(
            "payment_amount_unpublished",
            {limitation["code"] for limitation in data["limitations"]},
        )
        self.assertTrue(any(citation["page"] == 51 for citation in data["citations"]))

    def test_english_agreement_question_uses_structured_event_and_page_citation(self):
        response = self.ask("When was the agreement recorded?")

        data = response.json()["data"]
        self.assertEqual(data["route"], "DATABASE_QUERY")
        self.assertIn("2080/12/28 BS", data["answer"])
        self.assertTrue(any(citation["page"] == 51 for citation in data["citations"]))

    def test_anomaly_question_explains_event_gaps_without_accusation(self):
        evaluate_project(self.project)

        response = self.ask("Why is this project flagged?")

        data = response.json()["data"]
        self.assertEqual(data["route"], "ANOMALY_EXPLANATION")
        self.assertEqual(
            {anomaly["rule_id"] for anomaly in data["anomalies"]},
            {
                "AGREEMENT_DATE_CONTRACT_DETAILS_MISSING",
                "IMPLEMENTATION_PROGRESS_PERCENT_MISSING",
                "PAYMENT_DATE_AMOUNT_MISSING",
            },
        )
        self.assertTrue(all(citation["page"] == 51 for citation in data["citations"]))
        self.assertNotIn("fraud", data["answer"].casefold())
        self.assertNotIn("corruption", data["answer"].casefold())


@override_settings(
    INVESTIGATOR_ENABLE_GENERATION=False,
    VECTOR_DB_PROVIDER="database",
    INVESTIGATOR_TOP_K=6,
)
class SyntheticShowcaseInvestigatorTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)
        cls.project = Project.objects.get(pk=SHOWCASE_PROJECT_ID)
        materialize_reviewed_page_chunks(cls.project)

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("investigator-query")

    def ask(self, question):
        return self.client.post(
            self.url,
            {"question": question, "project_id": str(self.project.id)},
            format="json",
        )

    def test_complete_money_question_returns_citations_charts_and_synthetic_boundary(self):
        response = self.ask("Where did the project money go?")

        self.assertEqual(response.status_code, 200)
        data = response.json()["data"]
        self.assertEqual(data["route"], "PROJECT_INVESTIGATION")
        self.assertIn("NPR 10,000,000.00", data["answer"])
        self.assertIn("NPR 9,000,000.00", data["answer"])
        self.assertIn("NPR 7,200,000.00", data["answer"])
        self.assertIn("synthetic", data["answer"].casefold())
        self.assertEqual(data["limitations"], [])
        self.assertEqual(
            {chart["id"] for chart in data["visualizations"]},
            {"financial_flow", "payment_progress"},
        )
        progress_chart = next(
            chart for chart in data["visualizations"] if chart["id"] == "payment_progress"
        )
        self.assertEqual([row["value"] for row in progress_chart["data"]], [80.0, 58.0])
        self.assertTrue({1, 2, 3, 4} & {item["page"] for item in data["citations"]})

    def test_anomaly_answer_explains_synthetic_payment_progress_gap(self):
        evaluate_project(self.project)

        data = self.ask("Why is this project flagged?").json()["data"]

        self.assertEqual(data["route"], "ANOMALY_EXPLANATION")
        self.assertIn(
            "PAYMENT_PROGRESS_MISMATCH",
            {flag["rule_id"] for flag in data["anomalies"]},
        )
        self.assertIn("synthetic", data["answer"].casefold())
        self.assertNotIn("fraud", data["answer"].casefold())
