from decimal import Decimal

from budgets.management.commands.seed_demo_data import DEMO_PROJECT_ID
from django.core.management import call_command
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient


class ProjectDiscoveryApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data")

    def setUp(self):
        self.client = APIClient()

    def test_project_list_supports_search_filters_and_discovery_metadata(self):
        response = self.client.get(
            reverse("project-list"),
            {
                "search": "45/PMC/NCB/W/077-78",
                "fiscal_year__code": "2077-78",
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["pagination"]["count"], 1)
        project = response.data["data"][0]
        self.assertEqual(str(project["id"]), str(DEMO_PROJECT_ID))
        self.assertEqual(project["allocated_amount"], "800000.00")
        self.assertEqual(project["tender_count"], 1)
        self.assertEqual(project["evidence_count"], 0)

    def test_discovery_summary_keeps_unknown_allocations_separate(self):
        response = self.client.get(reverse("project-discovery-summary"))

        self.assertEqual(response.status_code, 200)
        totals = response.data["data"]["totals"]
        self.assertEqual(totals["project_count"], 9)
        self.assertEqual(totals["known_allocation_count"], 7)
        self.assertEqual(totals["unknown_allocation_count"], 2)
        self.assertEqual(totals["allocated_total"], "11950000.00")
        self.assertEqual(totals["procurement_project_count"], 4)
        self.assertEqual(totals["payment_reported_project_count"], 1)
        self.assertEqual(totals["geolocated_project_count"], 1)

    def test_rupa_filter_returns_five_official_allocated_projects(self):
        response = self.client.get(
            reverse("project-list"),
            {
                "local_government__code": "RUPA",
                "fiscal_year__code": "2080-81",
                "ward__number": 2,
            },
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["meta"]["pagination"]["count"], 5)
        projects = response.data["data"]
        self.assertEqual(
            sum((Decimal(project["allocated_amount"]) for project in projects), Decimal("0")),
            Decimal("1150000.00"),
        )
        self.assertTrue(all(project["data_classification"] == "official" for project in projects))
        self.assertTrue(all(project["status"] == "implementation" for project in projects))

    def test_discovery_summary_uses_the_same_filters_as_the_project_list(self):
        response = self.client.get(
            reverse("project-discovery-summary"),
            {
                "fiscal_year__code": "2078-79",
                "status": "unknown",
            },
        )

        self.assertEqual(response.status_code, 200)
        payload = response.data["data"]
        self.assertEqual(payload["totals"]["project_count"], 1)
        self.assertEqual(payload["totals"]["known_allocation_count"], 0)
        self.assertEqual(payload["totals"]["unknown_allocation_count"], 1)
        self.assertIsNone(payload["totals"]["allocated_total"])
        self.assertEqual(payload["by_fiscal_year"][0]["code"], "2078-79")
