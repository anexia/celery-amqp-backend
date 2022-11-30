from .backend import *


CELERY_RESULT_BACKEND = 'celery_amqp_backend.DirectReplyAMQPBackend://'
