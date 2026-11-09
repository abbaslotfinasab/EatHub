import json
import unittest
from unittest.mock import patch

from django.conf import settings

if not settings.configured:
    settings.configure(
        DEFAULT_CHARSET="utf-8",
        SECRET_KEY="test-only-not-a-real-secret",
        USE_I18N=False,
        DATABASES={"default": {"ENGINE": "django.db.backends.sqlite3", "NAME": ":memory:"}},
    )

from django.test import RequestFactory
from django.db import OperationalError

from EatHub.readiness import release_readiness


class ReleaseReadinessTests(unittest.TestCase):
    def setUp(self):
        self.factory = RequestFactory()

    def call_endpoint(self, method="get"):
        request = getattr(self.factory, method)("/api/ready/")
        return release_readiness(request)

    @patch("EatHub.readiness.connection.ensure_connection")
    def test_database_connection_returns_ready(self, ensure_connection):
        response = self.call_endpoint()

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            json.loads(response.content.decode()),
            {"status": "ready", "checks": {"database": "ok"}},
        )
        self.assertIn("no-store", response["Cache-Control"])
        ensure_connection.assert_called_once_with()

    @patch(
        "EatHub.readiness.connection.ensure_connection",
        side_effect=OperationalError("database unavailable"),
    )
    def test_database_failure_returns_not_ready_without_leaking_details(
        self, ensure_connection
    ):
        response = self.call_endpoint()

        self.assertEqual(response.status_code, 503)
        self.assertEqual(
            json.loads(response.content.decode()),
            {"status": "not_ready", "checks": {"database": "error"}},
        )
        self.assertNotIn("database unavailable", response.content.decode())
        self.assertIn("no-store", response["Cache-Control"])
        ensure_connection.assert_called_once_with()

    @patch("EatHub.readiness.connection.ensure_connection")
    def test_non_get_request_is_not_accepted(self, ensure_connection):
        response = self.call_endpoint(method="post")

        self.assertEqual(response.status_code, 405)
        self.assertIn("no-store", response["Cache-Control"])
        ensure_connection.assert_not_called()
