from django.test import TestCase
from django.urls import reverse


class HealthCheckTests(TestCase):
    """The health endpoint is the contract used to verify frontend/backend wiring."""

    def test_health_returns_ok(self) -> None:
        url = reverse("chatbot:health")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "nexus-backend"},
        )
