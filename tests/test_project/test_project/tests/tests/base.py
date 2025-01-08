import time

from django import test
from django.conf import settings

from celery.contrib.testing import worker

from test_project import *

__all__ = [
    "BaseIntegrationTestCase",
]


class BaseIntegrationTestCase(test.TransactionTestCase):
    """
    Base class for integration tests using api calls and the celery queue.
    """

    worker_controller = None
    worker_context = None

    @staticmethod
    def _get_celery_routes():
        celery_routes = getattr(settings, "CELERY_TASK_ROUTES", {})
        celery_queues = list(
            set(
                [
                    r.get("queue", settings.CELERY_TASK_DEFAULT_QUEUE)
                    for r in celery_routes.values()
                ]
                + [settings.CELERY_TASK_DEFAULT_QUEUE],
            ),
        )
        return celery_queues

    @classmethod
    def setUpClass(cls):
        celery_app.conf.task_reject_on_worker_lost = True
        celery_app.loader.import_module("celery.contrib.testing.tasks")

        worker.setup_app_for_worker(celery_app, None, None)

        cls.worker_context = worker.start_worker(
            celery_app,
            pool="solo",
            perform_ping_check=False,
            queues=cls._get_celery_routes(),
        )
        cls.worker_controller = cls.worker_context.__enter__()

        super().setUpClass()

    @classmethod
    def tearDownClass(cls):
        celery_app.control.purge()

        # give the async jobs some time to finish.
        time.sleep(10)

        try:
            cls.worker_context.__exit__(None, None, None)
        except RuntimeError:
            pass

        super().tearDownClass()
