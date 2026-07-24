from accounts.models import CitizenProfile
from budgets.management.commands.seed_demo_data import DEMO_PROJECT_ID
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.db import IntegrityError, transaction
from django.test import TestCase
from django.urls import reverse
from projects.models import Project
from rest_framework.test import APIClient

from feedback.models import CitizenFeedback, FeedbackRevision

User = get_user_model()


class CitizenFeedbackApiTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data")
        cls.project = Project.objects.get(pk=DEMO_PROJECT_ID)

    def setUp(self):
        self.user = User.objects.create_user(
            username="feedback-citizen",
            password="safe-demo-password-123",
        )
        self.profile = CitizenProfile.objects.create(
            user=self.user,
            role=CitizenProfile.Role.VERIFIED_CITIZEN,
            citizen_key="c" * 64,
            verified_municipality_code="PKR",
            verified_ward_number=8,
            verified_at=self.project.updated_at,
        )
        self.client = APIClient()
        self.client.force_login(self.user)
        self.payload = {
            "project": str(self.project.pk),
            "completion_rating": 3,
            "quality_rating": 4,
            "usefulness_rating": 5,
            "allocation_fairness_rating": 3,
            "comment": "Observed the road condition directly.",
            "directly_observed": True,
        }

    def test_one_feedback_per_citizen_project_with_idempotent_retry(self):
        first = self.client.post(
            reverse("feedback-list"),
            self.payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="submission-001",
        )
        self.assertEqual(first.status_code, 201)
        self.assertEqual(first.data["data"]["verification_status"], "verified_local")

        retry = self.client.post(
            reverse("feedback-list"),
            self.payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="submission-001",
        )
        self.assertEqual(retry.status_code, 200)
        self.assertEqual(retry.data["data"]["id"], first.data["data"]["id"])

        duplicate = self.client.post(
            reverse("feedback-list"),
            self.payload,
            format="json",
            HTTP_IDEMPOTENCY_KEY="submission-002",
        )
        self.assertEqual(duplicate.status_code, 409)
        self.assertEqual(duplicate.data["errors"][0]["code"], "duplicate_feedback")
        self.assertEqual(CitizenFeedback.objects.count(), 1)

    def test_feedback_can_be_edited_and_revision_is_audited(self):
        created = self.client.post(reverse("feedback-list"), self.payload, format="json")
        feedback_id = created.data["data"]["id"]
        updated = self.client.patch(
            reverse("feedback-detail", kwargs={"pk": feedback_id}),
            {"quality_rating": 2, "comment": "Updated after another visit."},
            format="json",
        )
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.data["data"]["quality_rating"], 2)
        self.assertEqual(FeedbackRevision.objects.filter(feedback_id=feedback_id).count(), 1)

    def test_rating_constraint_and_public_aggregate_groups(self):
        invalid = self.client.post(
            reverse("feedback-list"),
            {**self.payload, "completion_rating": 6},
            format="json",
        )
        self.assertEqual(invalid.status_code, 400)

        self.client.post(reverse("feedback-list"), self.payload, format="json")
        summary = self.client.get(
            reverse("feedback-summary"),
            {"project": str(self.project.pk)},
        )
        self.assertEqual(summary.status_code, 200)
        self.assertEqual(summary.data["data"]["all_citizens"]["count"], 1)
        self.assertEqual(summary.data["data"]["verified_citizens"]["count"], 1)
        self.assertEqual(summary.data["data"]["verified_local_residents"]["count"], 1)

    def test_database_constraint_blocks_direct_duplicate(self):
        values = {
            "citizen_profile": self.profile,
            "project": self.project,
            "completion_rating": 3,
            "quality_rating": 3,
            "usefulness_rating": 3,
            "allocation_fairness_rating": 3,
        }
        CitizenFeedback.objects.create(**values)
        with self.assertRaises(IntegrityError), transaction.atomic():
            CitizenFeedback.objects.create(**values)

    def test_anonymous_submission_is_rejected(self):
        self.client.logout()
        response = self.client.post(reverse("feedback-list"), self.payload, format="json")
        self.assertEqual(response.status_code, 403)
