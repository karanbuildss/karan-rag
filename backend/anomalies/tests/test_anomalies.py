from budgets.management.commands.seed_demo_data import DEMO_PROJECT_ID
from config.models import DataClassification
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from documents.models import ProjectDocumentLink, SourceDocument
from projects.models import Project
from rest_framework.test import APIClient

from anomalies.models import AnomalyFlag
from anomalies.services import evaluate_project


class ExplainableAnomalyTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data")
        cls.project = Project.objects.get(pk=DEMO_PROJECT_ID)
        audit = SourceDocument.objects.create(
            title_en="Official audit test source",
            title_np="आधिकारिक लेखापरीक्षण परीक्षण स्रोत",
            document_type=SourceDocument.DocumentType.AUDIT_REPORT,
            local_government=cls.project.local_government,
            fiscal_year=cls.project.fiscal_year,
            language=SourceDocument.Language.NEPALI,
            original_filename="audit.pdf",
            source_url="https://oag.gov.np/reports/local-level-report",
            source_url_kind=SourceDocument.SourceUrlKind.LANDING_PAGE,
            data_classification=DataClassification.OFFICIAL,
            page_count=100,
        )
        ProjectDocumentLink.objects.create(
            project=cls.project,
            document=audit,
            relationship=ProjectDocumentLink.Relationship.AUDIT,
            page_from=48,
            page_to=48,
            section="Advance review",
            evidence_note_en="The audit source contains a related Jalpa Marg reference.",
        )
        procurement = SourceDocument.objects.create(
            title_en="Official procurement test source",
            title_np="आधिकारिक खरिद परीक्षण स्रोत",
            document_type=SourceDocument.DocumentType.PROCUREMENT_NOTICE,
            local_government=cls.project.local_government,
            fiscal_year=cls.project.fiscal_year,
            language=SourceDocument.Language.MIXED,
            original_filename="tender.pdf",
            source_url="https://bolpatra.gov.np/egp/searchOpportunity",
            source_url_kind=SourceDocument.SourceUrlKind.LANDING_PAGE,
            data_classification=DataClassification.OFFICIAL,
            page_count=10,
        )
        ProjectDocumentLink.objects.create(
            project=cls.project,
            document=procurement,
            relationship=ProjectDocumentLink.Relationship.PROCUREMENT,
            page_from=1,
            page_to=1,
            section="Invitation for bids",
            evidence_note_en="The official notice records the tender estimate.",
        )

    def test_rules_explain_evidence_gaps_without_accusations(self):
        flags = evaluate_project(self.project)
        rule_ids = {flag.rule_id for flag in flags}
        self.assertIn("EVIDENCE_AWARD_MISSING", rule_ids)
        self.assertIn("EVIDENCE_PAYMENT_MISSING", rule_ids)
        self.assertIn("EVIDENCE_PROGRESS_MISSING", rule_ids)
        self.assertIn("LINKED_SCOPE_AMOUNT_GAP", rule_ids)
        self.assertIn("OFFICIAL_AUDIT_REFERENCE_REVIEW", rule_ids)

        amount_gap = AnomalyFlag.objects.get(
            project=self.project,
            rule_id="LINKED_SCOPE_AMOUNT_GAP",
        )
        self.assertEqual(amount_gap.reliability, AnomalyFlag.Reliability.LIMITED)
        self.assertEqual(amount_gap.calculated_values["estimate_to_allocation_ratio"], "11.85")
        combined_text = f"{amount_gap.title_en} {amount_gap.reason_en}".lower()
        self.assertNotIn("fraud", combined_text)
        self.assertNotIn("corruption", combined_text)
        self.assertTrue(amount_gap.source_references)
        self.assertTrue(
            all(
                {"en", "np"} <= explanation.keys()
                for explanation in amount_gap.possible_explanations
            )
        )

    def test_evaluation_is_idempotent_and_api_is_filterable(self):
        evaluate_project(self.project)
        evaluate_project(self.project)
        self.assertEqual(
            AnomalyFlag.objects.filter(project=self.project).values("rule_id").distinct().count(),
            AnomalyFlag.objects.filter(project=self.project).count(),
        )

        response = APIClient().get(
            reverse("anomaly-list"),
            {"project__code": self.project.code, "status": "active"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["pagination"]["count"], 5)
