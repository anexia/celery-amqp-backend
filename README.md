celery-amqp-backend
===================

[![PyPI](https://img.shields.io/pypi/v/celery-amqp-backend)](https://pypi.org/project/celery-amqp-backend/)
[![Test Status](https://github.com/anexia/celery-amqp-backend/actions/workflows/test.yml/badge.svg?branch=main)](https://github.com/anexia/celery-amqp-backend/actions/workflows/test.yml)
[![Codecov](https://codecov.io/gh/anexia/celery-amqp-backend/branch/main/graph/badge.svg)](https://codecov.io/gh/anexia/celery-amqp-backend)

`celery-amqp-backend` is a rewrite of the Celery's original `amqp://` result backend, which was removed from Celery
with version 5.0. Celery encourages you to use the newer `rpc://` result backend, as it does not create a new
result queue for each task and thus is faster in many circumstances. However, it's not always possible to switch
to the new `rpc://` result backend, as it does have restrictions as follows:
 - `rpc://` does not support chords.
 - `rpc://` results may hold a wrong state.
 - `rpc://` may lose results when using `gevent` or `greenlet`.

The result backend `celery_amqp_backend.AMQPBackend://` does not suffer from the same issues.

# Installation

With a [correctly configured](https://pipenv.pypa.io/en/latest/basics/#basic-usage-of-pipenv) `pipenv` toolchain:

```sh
pipenv install celery-amqp-backend
```

You may also use classic `pip` to install the package:

```sh
pip install celery-amqp-backend
```

# Getting started

## Configuration options

### `result_backend: str`

Set to `'celery_amqp_backend.AMQPBackend://'` to use this result backend.

### `result_persistent: bool`

Default: `False`

If set to `True`, result queues will be persistent queues. This means that messages will not be lost after a
message broker restart.

### `result_exchange: str`

Default: `'celery_result'`

The prefix for result queues created by the backend (e.g. if `result_exchange` is set to `'example'`, a result
queue may be named `'example.36723ac0-aacf-4668-8927-08794d0b082e'`).

### `result_exchange_type: str`

Default: `'direct'`

The type of the exchange created by the backend (e.g. `'direct'`, `'topic'` etc.).

## Example configuration

```python
result_backend = 'celery_amqp_backend.AMQPBackend://'
result_persistent = False
result_exchange = 'celery_result'
result_exchange_type = 'direct'
```

# Supported versions

|             | Celery 5.2 | Celery 5.3 |
|-------------|------------|------------|
| Python 3.8  | ✓          | ✓          |
| Python 3.9  | ✓          | ✓          |
| Python 3.10 | ✓          | ✓          |
| Python 3.11 | ✓          | ✓          |
| Python 3.12 | ✗          | ✓          |

# List of developers

* Andreas Stocker <AStocker@anexia-it.com>, Lead Developer
