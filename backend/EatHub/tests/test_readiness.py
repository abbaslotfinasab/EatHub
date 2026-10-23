import json
import os
import unittest
from unittest.mock import patch

from django.conf import settings

if not settings.configured:
    settings.configure(
        DEFAULT_CHARSET="utf-8",
        SECRET_KEY="test-only-not-a-real-secret",
        USE_I18N=False,
    )

from django.test import RequestFactory

from EatHub.readiness import release_readiness


VALID_RELEASE_ID = "success-20261022t010203z-0123456789ab-abcdef01"


class ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def call_endpoint(self, method="get"):
        request = getattr(self.factory, method)("/api/ready/")
        return release_readiness(request)

    def test_valid_configured_release_returns_only_release_identity(self):
        with patch.dict(os.environ, {"EATHUB_RELEASE_ID": VALID_RELEASE_ID}):
            response = self.call_endpoint()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/plain; charset=utf-8")
        self.assertIn("no-store", response["Cache-Control"])
        self.assertEqual(response.content.decode(), f"ready:{VALID_RELEASE_ID}")

    def test_missing_or_malformed_identity_fails_closed_without_echoing_value(self):
        for invalid_value in (None, "", "success-20261399t256199z-0123456789ab-abcdef01", "secret-value"):
            with self.subTest(identity=invalid_value), patch.dict(os.environ, {}, clear=False):
                os.environ.pop("EATHUB_RELEASE_ID", None)
                if invalid_value is not None:
                    os.environ["EATHUB_RELEASE_ID"] = invalid_value

                response = self.call_endpoint()

                self.assertEqual(response.status_code, 503)
                self.assertIn("no-store", response["Cache-Control"])
                self.assertEqual(json.loads(response.content.decode()), {"status": "not_ready"})
                self.assertNotIn("secret-value", response.content.decode())

    def test_non_get_request_is_not_accepted(self):
        with patch.dict(os.environ, {"EATHUB_RELEASE_ID": VALID_RELEASE_ID}):
            response = self.call_endpoint(method="post")

        self.assertEqual(response.status_code, 405)
        self.assertIn("no-store", response["Cache-Control"])
