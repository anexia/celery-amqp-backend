import time

from test_project import *

__all__ = [
    'sum_numbers',
    'add_numbers',
    'add_numbers_slow',
    'combine_lists',
    'combine_dicts',
]


@celery_app.task
def sum_numbers(numbers):
    return sum(numbers)


@celery_app.task
def add_numbers(x, y):
    return x + y


@celery_app.task
def add_numbers_slow(x, y):
    time.sleep(10)
    return x + y


@celery_app.task
def combine_lists(x, y):
    return x + y


@celery_app.task
def combine_dicts(x, y):
    x.update(y)
    return x
