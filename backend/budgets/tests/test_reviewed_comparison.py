import csv
import hashlib
from decimal import Decimal
from pathlib import Path
from tempfile import TemporaryDirectory

from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from documents.models import SourceDocument
from geography.models import LocalGovernment
from rest_framework.test import APIClient

from budgets.models import BudgetAllocation, FiscalYear, SubSector
from budgets.services import import_reviewed_budget_facts


class ReviewedBudgetComparisonTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)
        cls.kathmandu = LocalGovernment.objects.get(code="KMC")
        cls.hetauda = LocalGovernment.objects.get(code="HETAUDA")
        cls.fiscal_year = FiscalYear.objects.get(code="2081-82")
        cls.infrastructure = SubSector.objects.get(code="INF-ALL")
        cls.document = SourceDocument.objects.create(
            title_en="Kathmandu reviewed expenditure",
            title_np="काठमाडौं समीक्षा गरिएको खर्च",
            document_type=SourceDocument.DocumentType.EXPENDITURE_REPORT,
            local_government=cls.kathmandu,
            fiscal_year=cls.fiscal_year,
            language=SourceDocument.Language.NEPALI,
            file_format=SourceDocument.FileFormat.IMAGE,
            original_filename="sector-summary.png",
            sha256="b" * 64,
            source_url="https://new.kathmandu.gov.np/official-source",
            page_count=1,
        )
        BudgetAllocation.objects.create(
            local_government=cls.kathmandu,
            fiscal_year=cls.fiscal_year,
            subsector=cls.infrastructure,
            budget_type=BudgetAllocation.BudgetType.TOTAL,
            allocated_amount=Decimal("1000.00"),
            spent_amount=Decimal("525.40"),
            source_document=cls.document,
            source_page=1,
            review_status=BudgetAllocation.ReviewStatus.REVIEWED,
            reliability=BudgetAllocation.Reliability.STRONG,
            comparability=BudgetAllocation.Comparability.STRONG,
            source_scope_en="Reviewed broad infrastructure total.",
            source_scope_np="समीक्षा गरिएको बृहत् पूर्वाधार जम्मा।",
            data_classification="official",
            source_url=cls.document.source_url,
        )
        BudgetAllocation.objects.create(
            local_government=cls.hetauda,
            fiscal_year=cls.fiscal_year,
            subsector=cls.infrastructure,
            budget_type=BudgetAllocation.BudgetType.TOTAL,
            allocated_amount=Decimal("900.00"),
            spent_amount=Decimal("300.00"),
            review_status=BudgetAllocation.ReviewStatus.REVIEW_REQUIRED,
            data_classification="official",
        )

    def setUp(self):
        self.client = APIClient()

    def test_comparison_returns_only_reviewed_page_cited_values(self):
        response = self.client.get(
            reverse("budget-allocation-comparison"),
            {"fiscal_year": "2081-82"},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.data["data"]
        self.assertEqual(payload["evidence_summary"]["record_count"], 1)
        self.assertTrue(payload["evidence_summary"]["reviewed_only"])
        record = payload["records"][0]
        self.assertEqual(record["local_government_code"], "KMC")
        self.assertEqual(record["utilization_percent"], "52.54")
        self.assertEqual(record["comparability"], "strong")
        self.assertEqual(record["citation"]["page"], 1)
        self.assertEqual(
            set(record["citation"]),
            {
                "document_id",
                "document_title",
                "document_title_np",
                "page",
                "section",
                "source_url",
            },
        )

    def test_comparison_filters_by_sector_and_returns_honest_empty_state(self):
        response = self.client.get(
            reverse("budget-allocation-comparison"),
            {"fiscal_year": "2081-82", "sector": "SOC"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["data"]["records"], [])
        self.assertIsNone(response.data["data"]["fiscal_year"])


class ReviewedBudgetFactImportTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)

    def test_import_requires_registered_hash_and_preserves_page_provenance(self):
        with TemporaryDirectory() as dataset_dir:
            dataset_root = Path(dataset_dir)
            evidence = dataset_root / "reviewed.pdf"
            evidence.write_bytes(b"registered official evidence")
            local_government = LocalGovernment.objects.get(code="KMC")
            fiscal_year = FiscalYear.objects.get(code="2081-82")
            document = SourceDocument.objects.create(
                title_en="Registered reviewed statement",
                document_type=SourceDocument.DocumentType.EXPENDITURE_REPORT,
                local_government=local_government,
                fiscal_year=fiscal_year,
                language=SourceDocument.Language.NEPALI,
                original_filename=evidence.name,
                sha256=hashlib.sha256(evidence.read_bytes()).hexdigest(),
                source_url="https://new.kathmandu.gov.np/reviewed",
                page_count=1,
            )
            facts_path = dataset_root / "verified_budget_facts.csv"
            fieldnames = [
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
            ]
            with facts_path.open("w", encoding="utf-8", newline="") as output:
                writer = csv.DictWriter(output, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerow(
                    {
                        "local_government_code": "KMC",
                        "fiscal_year_code": "2081-82",
                        "subsector_code": "ECO-ALL",
                        "budget_type": "total",
                        "allocated_amount": "100.00",
                        "spent_amount": "25.00",
                        "source_relative_path": evidence.name,
                        "source_page": "1",
                        "review_status": "reviewed",
                        "reliability": "strong",
                        "comparability": "strong",
                        "source_scope_en": "Reviewed sector statement.",
                        "source_scope_np": "समीक्षा गरिएको क्षेत्रगत विवरण।",
                        "data_classification": "official",
                    }
                )

            imported = import_reviewed_budget_facts(facts_path)

        self.assertEqual(len(imported), 1)
        allocation = imported[0]
        self.assertEqual(allocation.source_document_id, document.id)
        self.assertEqual(allocation.source_page, 1)
        self.assertEqual(allocation.review_status, "reviewed")
        self.assertEqual(allocation.spent_amount, Decimal("25.00"))
