import celery.exceptions

__all__ = [
    "AMQPBacklogLimitExceededException",
    "AMQPWaitEmptyException",
    "AMQPWaitTimeoutException",
]


class BaseCeleryException(Exception):
    """
    Base class for all celery related exceptions within the application.
    """

    _msg_template = None

    def __init__(self, *args, internal_exception=None, **kwargs):
        self.internal_exception = internal_exception

        super().__init__(self._msg_template.format(*args, **kwargs))


class AMQPBacklogLimitExceededException(BaseCeleryException):
    _msg_template = 'Too much state history to fast-forward for task "{task}".'


class AMQPWaitEmptyException(BaseCeleryException):
    _msg_template = 'No message got drained from the queue while waiting for "{task}".'


class AMQPWaitTimeoutException(BaseCeleryException, celery.exceptions.TimeoutError):
    _msg_template = "The operation timed out."
