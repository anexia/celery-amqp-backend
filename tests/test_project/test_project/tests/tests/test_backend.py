import time
import celery

from celery_amqp_backend import *

from test_project.tests.tasks import *

from .base import *

__all__ = [
    "BackendTestCase",
]


class BackendTestCase(BaseIntegrationTestCase):
    fixtures = []

    def test_async_result(self):
        self.assertEqual(add_numbers.delay(1, 2).get(), 3)
        self.assertEqual(combine_lists.delay([1, 2], [3, 4]).get(), [1, 2, 3, 4])
        self.assertEqual(
            combine_dicts.delay({"a": "abc"}, {"b": "efg"}).get(),
            {"a": "abc", "b": "efg"},
        )

    def test_async_result_status(self):
        async_result = add_numbers_slow.delay(1, 2)

        self.assertEqual(async_result.ready(), False)
        self.assertEqual(async_result.successful(), False)

        time.sleep(30)

        self.assertEqual(async_result.ready(), True)
        self.assertEqual(async_result.successful(), True)

    def test_async_result_group(self):
        async_job = celery.group(
            [
                add_numbers.s(1, 2),
                combine_lists.s([1, 2], [3, 4]),
                combine_dicts.s({"a": "abc"}, {"b": "efg"}),
            ],
        )
        async_result = async_job.apply_async()
        result = async_result.get()

        self.assertEqual(result[0], 3)
        self.assertEqual(result[1], [1, 2, 3, 4])
        self.assertEqual(result[2], {"a": "abc", "b": "efg"})

    def test_async_result_group_status(self):
        async_job = celery.group(
            [
                add_numbers.s(1, 2),
                add_numbers_slow.s(1, 2),
                combine_lists.s([1, 2], [3, 4]),
                combine_dicts.s({"a": "abc"}, {"b": "efg"}),
            ],
        )
        async_result = async_job.apply_async()

        self.assertEqual(async_result.ready(), False)
        self.assertEqual(async_result.successful(), False)

        time.sleep(30)

        self.assertEqual(async_result.ready(), True)
        self.assertEqual(async_result.successful(), True)

    def test_async_result_chord(self):
        async_chord = celery.chord(
            [
                add_numbers.s(1, 2),
                add_numbers_slow.s(3, 4),
            ],
        )
        async_result = async_chord(sum_numbers.s())
        result = async_result.get()

        self.assertEqual(result, 10)

    def test_async_result_chord_status(self):
        async_chord = celery.chord(
            [
                add_numbers.s(1, 2),
                add_numbers_slow.s(3, 4),
            ],
        )
        async_result = async_chord(sum_numbers.s())

        self.assertEqual(async_result.ready(), False)
        self.assertEqual(async_result.successful(), False)

        time.sleep(30)

        self.assertEqual(async_result.ready(), True)
        self.assertEqual(async_result.successful(), True)

    def test_async_result_timeout(self):
        with self.assertRaises(AMQPWaitTimeoutException):
            async_result = add_numbers_slow.delay(1, 2)
            async_result.get(timeout=5)
