from datetime import date
from decimal import Decimal

from budgets.management.commands.seed_demo_data import (
    DEMO_PROJECT_ID,
    FOLLOW_UP_PROJECT_ID,
    FOOTPATH_PROJECT_ID,
)
from budgets.models import BudgetAllocation
from django.core.management import call_command
from django.db import IntegrityError, connection, transaction
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from payments.models import Payment
from procurement.models import ContractAward, Contractor, Tender
from rest_framework.test import APIClient

from projects.models import Project


class MoneyTrailApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)

    def setUp(self):
        self.client = APIClient()
        self.url = reverse("project-money-trail", kwargs={"pk": DEMO_PROJECT_ID})

    def test_money_trail_keeps_unsupported_real_fields_unknown(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["errors"], [])
        self.assertEqual(payload["data"]["project"]["code"], "PKR-W08-JALPA-2077-78")
        self.assertEqual(
            payload["data"]["project"]["data_classification"],
            "reconstructed_from_official_sources",
        )
        self.assertEqual(payload["data"]["project"]["status"], "unknown")
        self.assertEqual(payload["data"]["financial_summary"]["allocated_amount"], "800000.00")
        self.assertIsNone(payload["data"]["financial_summary"]["contracted_amount"])
        self.assertIsNone(payload["data"]["financial_summary"]["reported_paid_amount"])
        self.assertIsNone(payload["data"]["financial_summary"]["reported_contract_balance"])
        self.assertEqual(
            payload["data"]["financial_summary"]["payment_reporting_status"],
            "not_yet_reported",
        )
        self.assertEqual(len(payload["data"]["procurement"]), 1)
        tender = payload["data"]["procurement"][0]
        self.assertEqual(tender["reference"], "45/PMC/NCB/W/077-78")
        self.assertEqual(tender["invitation_number"], "16.1/PMC/077-78")
        self.assertEqual(tender["estimated_amount"], "9477987.16")
        self.assertEqual(tender["bid_security_amount"], "270000.00")
        self.assertIsNone(tender["award"])
        self.assertEqual(payload["data"]["payments"], [])
        self.assertEqual(payload["data"]["milestones"], [])
        self.assertIsNone(payload["data"]["project"]["location"])

    def test_missing_payment_records_are_not_reported_as_zero(self):
        Payment.objects.all().delete()

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        summary = response.json()["data"]["financial_summary"]
        self.assertIsNone(summary["reported_paid_amount"])
        self.assertIsNone(summary["reported_contract_balance"])
        self.assertEqual(summary["payment_reporting_status"], "not_yet_reported")

    def test_money_trail_query_count_is_bounded(self):
        with CaptureQueriesContext(connection) as queries:
            response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertLessEqual(len(queries), 8)

    def test_project_list_filters_and_uses_response_envelope(self):
        response = self.client.get(reverse("project-list"), {"local_government__code": "PKR"})

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["meta"]["pagination"]["count"], 3)
        self.assertIn(str(DEMO_PROJECT_ID), {item["id"] for item in payload["data"]})

    def test_seed_command_is_idempotent(self):
        call_command("seed_demo_data", verbosity=0)

        self.assertEqual(Project.objects.filter(pk=DEMO_PROJECT_ID).count(), 1)
        self.assertEqual(Project.objects.count(), 3)
        self.assertEqual(Tender.objects.count(), 3)
        self.assertEqual(ContractAward.objects.count(), 0)
        self.assertEqual(Payment.objects.count(), 0)
        self.assertEqual(
            Project.objects.get(pk=DEMO_PROJECT_ID).data_classification,
            "reconstructed_from_official_sources",
        )

    def test_separate_later_procurements_do_not_invent_allocations(self):
        follow_up = Project.objects.get(pk=FOLLOW_UP_PROJECT_ID)
        footpath = Project.objects.get(pk=FOOTPATH_PROJECT_ID)

        self.assertIsNone(follow_up.allocated_amount)
        self.assertIsNone(follow_up.budget_allocation)
        self.assertEqual(follow_up.tenders.get().reference, "149/PMC/NCB/W/078-079")
        self.assertIsNone(footpath.allocated_amount)
        self.assertEqual(
            footpath.tenders.get().estimated_amount,
            Decimal("2217190.45"),
        )

    def test_database_rejects_negative_payment(self):
        project = Project.objects.get(pk=DEMO_PROJECT_ID)
        contractor = Contractor.objects.create(
            name="Constraint test contractor",
            registration_number="CONSTRAINT-TEST",
        )
        tender = Tender.objects.create(
            project=project,
            reference="CONSTRAINT-TENDER",
            title_en="Constraint test tender",
            title_np="परीक्षण बोलपत्र",
            procurement_method=Tender.ProcurementMethod.OTHER,
        )
        award = ContractAward.objects.create(
            tender=tender,
            contractor=contractor,
            award_reference="CONSTRAINT-AWARD",
            contract_amount=Decimal("1.00"),
        )

        with self.assertRaises(IntegrityError), transaction.atomic():
            Payment.objects.create(
                contract_award=award,
                reference="NEGATIVE-PAYMENT-TEST",
                amount=Decimal("-1.00"),
                paid_on=date(2021, 1, 1),
            )

    def test_database_rejects_negative_bid_security(self):
        tender = Tender.objects.get(reference="45/PMC/NCB/W/077-78")
        tender.bid_security_amount = Decimal("-1.00")

        with self.assertRaises(IntegrityError), transaction.atomic():
            tender.save(update_fields=["bid_security_amount"])

    def test_database_rejects_duplicate_budget_dimension(self):
        allocation = BudgetAllocation.objects.get()
        allocation.pk = None

        with self.assertRaises(IntegrityError), transaction.atomic():
            allocation.save()
