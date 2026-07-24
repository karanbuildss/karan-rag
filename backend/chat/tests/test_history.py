from budgets.services.showcase import SHOWCASE_PROJECT_ID
from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase, override_settings
from django.urls import reverse
from rest_framework.test import APIClient

from chat.models import ChatSession

User = get_user_model()


@override_settings(INVESTIGATOR_ENABLE_GENERATION=False)
class ChatHistoryTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        call_command("seed_demo_data", verbosity=0)
        cls.user = User.objects.create_user(
            username="history-owner",
            password="safe-demo-password-123",
        )
        cls.other = User.objects.create_user(
            username="history-other",
            password="safe-demo-password-123",
        )

    def setUp(self):
        self.client = APIClient()

    def test_authenticated_question_is_saved_and_private(self):
        self.client.force_login(self.user)
        response = self.client.post(
            reverse("investigator-query"),
            {
                "question": "How much was paid?",
                "project_id": SHOWCASE_PROJECT_ID,
                "language": "en",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        session_id = response.data["data"]["session_id"]
        session = ChatSession.objects.get(pk=session_id)
        self.assertEqual(session.user, self.user)
        self.assertEqual(session.messages.count(), 2)
        self.assertEqual(session.messages.last().route_used, "DATABASE_QUERY")
        self.assertTrue(session.messages.last().response_visualizations)

        own_history = self.client.get(reverse("chat-session-list"))
        self.assertEqual(own_history.status_code, 200)
        self.assertEqual(own_history.data["data"][0]["id"], str(session.id))

        self.client.force_login(self.other)
        other_history = self.client.get(reverse("chat-session-list"))
        self.assertEqual(other_history.data["data"], [])
        hidden = self.client.get(reverse("chat-session-detail", kwargs={"pk": session.pk}))
        self.assertEqual(hidden.status_code, 404)

    def test_guest_question_is_not_saved(self):
        response = self.client.post(
            reverse("investigator-query"),
            {
                "question": "How much was paid?",
                "project_id": SHOWCASE_PROJECT_ID,
                "language": "en",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.data["data"]["session_id"])
        self.assertEqual(ChatSession.objects.count(), 0)
