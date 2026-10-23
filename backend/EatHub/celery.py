import os

from celery import Celery


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "EatHub.settings")

app = Celery("EatHub")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()
