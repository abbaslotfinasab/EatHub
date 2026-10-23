from celery import shared_task


@shared_task(name="eathub.tests.celery_test_app.autodiscovery_probe")
def autodiscovery_probe():
    return "discovered"
