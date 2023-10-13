from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-7db3wq7w6q@g3h^al9&ji=una44&ba+i#pz=@q=$+#&cx6%@$g'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'test_project.tests',
]

MIDDLEWARE = []

ROOT_URLCONF = 'test_project.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'test_project.wsgi.application'


# Database
# https://docs.djangoproject.com/en/3.2/ref/settings/#databases

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}


# Password validation
# https://docs.djangoproject.com/en/3.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = []


# Internationalization
# https://docs.djangoproject.com/en/3.2/topics/i18n/

LANGUAGE_CODE = 'en-gb'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.2/howto/static-files/

STATIC_URL = '/static/'

# Default primary key field type
# https://docs.djangoproject.com/en/3.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'


# Celery Setup
# http://docs.celeryproject.org/en/latest/django/first-steps-with-django.html
CELERY_BROKER_URL = 'amqp://127.0.0.1/'
CELERY_RESULT_BACKEND = 'celery_amqp_backend.AMQPBackend://'
CELERY_BROKER_POOL_LIMIT = 10
CELERY_TASK_DEFAULT_QUEUE = 'tests.default'
CELERY_EVENT_QUEUE_PREFIX = 'tests.event'
CELERY_RESULT_EXCHANGE = 'tests.result'
CELERY_EVENT_EXCHANGE = 'tests.event'
CELERY_CONTROL_EXCHANGE = 'tests.control'
CELERY_ACCEPT_CONTENT = [
    'json',
]
CELERY_TASK_DEFAULT_DELIVERY_MODE = 'transient'
CELERY_RESULT_EXPIRES = 60
CELERY_RESULT_PERSISTENT = False
CELERY_TASK_ACKS_LATE = False
CELERY_TASK_TRACK_STARTED = False
CELERY_TASK_IGNORE_RESULT = False
CELERY_WORKER_PREFETCH_MULTIPLIER = 1
