from django.test import Client, SimpleTestCase
from django.urls import reverse


class HealthCheckTests(SimpleTestCase):
    def test_health_check_returns_stable_success_envelope(self):
        response = Client().get(reverse("health-check"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "data": {"service": "budget-darpan-api", "status": "ok"},
                "meta": {},
                "errors": [],
            },
        )

    def test_health_check_rejects_non_get_requests(self):
        response = Client().post(reverse("health-check"))

        self.assertEqual(response.status_code, 405)
