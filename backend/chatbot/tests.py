from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from chatbot.services.storage import _object_url, _safe_filename


class HealthCheckTests(TestCase):
    """The health endpoint is the contract used to verify frontend/backend wiring."""

    def test_health_returns_ok(self) -> None:
        url = reverse("chatbot:health")
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {"status": "ok", "service": "nexus-backend", "database": "ok"},
        )


class StoragePathTests(SimpleTestCase):
    """Regression guards for the two upload-path defects found by E2E.

    French filenames broke uploads twice: first with a UnicodeEncodeError
    (raw é in the request URL), then with Supabase's "Invalid key" rejection
    of non-ASCII object keys.
    """

    def test_safe_filename_transliterates_accents_to_ascii(self) -> None:
        self.assertEqual(
            _safe_filename("Mémoire LungCancer IA.pdf"),
            "Memoire_LungCancer_IA.pdf",
        )
        self.assertEqual(_safe_filename("MémoireTemplate.zip"), "MemoireTemplate.zip")

    def test_safe_filename_falls_back_when_nothing_is_left(self) -> None:
        self.assertEqual(_safe_filename(""), "document.pdf")
        self.assertEqual(_safe_filename("   "), "document.pdf")

    def test_object_url_keeps_plain_ascii_keys_untouched(self) -> None:
        # Previously-working keys must stay byte-identical (no regression).
        url = _object_url(
            "https://proj.supabase.co", "documents", "student/abc123-report.pdf"
        )
        self.assertEqual(
            url, "https://proj.supabase.co/storage/v1/object/documents/student/abc123-report.pdf"
        )

    def test_object_url_percent_encodes_and_round_trips(self) -> None:
        from urllib.parse import unquote

        key = "student/abc123-a b#c.pdf"
        url = _object_url("https://proj.supabase.co", "documents", key)
        self.assertTrue(url.isascii())  # urllib refuses anything else
        path = url.split("/storage/v1/object/", 1)[1]
        self.assertTrue(path.startswith("documents/"))
        self.assertEqual(unquote(path), f"documents/{key}")
