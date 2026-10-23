from pathlib import Path

from celery.app.utils import find_app
from django.conf import settings
from django.test import SimpleTestCase

from EatHub.celery import app


class CeleryConfigurationTests(SimpleTestCase):
    def test_canonical_cli_target_resolves_to_project_app(self):
        self.assertIs(find_app("EatHub.celery:app"), app)
        self.assertEqual(app.main, "EatHub")

    def test_django_settings_are_loaded_with_celery_namespace(self):
        self.assertTrue(app.conf.broker_url == settings.CELERY_BROKER_URL)
        self.assertTrue(app.conf.result_backend == settings.CELERY_RESULT_BACKEND)
        self.assertEqual(app.conf.task_serializer, "json")
        self.assertEqual(app.conf.result_serializer, "json")
        self.assertEqual(app.conf.accept_content, ["json"])
        self.assertEqual(app.conf.timezone, settings.TIME_ZONE)
        self.assertEqual(app.conf.enable_utc, settings.USE_TZ)
        self.assertTrue(app.conf.broker_connection_retry_on_startup)

    def test_autodiscovery_loads_a_test_only_tasks_module(self):
        app.autodiscover_tasks(
            packages=["EatHub.tests.celery_test_app"], force=True
        )
        self.assertIn("eathub.tests.celery_test_app.autodiscovery_probe", app.tasks)

    def test_compose_worker_uses_the_canonical_target(self):
        compose_path = (
            Path(__file__).resolve().parents[3]
            / "deployment"
            / "docker-compose.yml"
        )
        target_line = "command: celery -A EatHub.celery:app worker -l info"
        self.assertTrue(
            any(
                line.strip() == target_line
                for line in compose_path.read_text().splitlines()
            )
        )
