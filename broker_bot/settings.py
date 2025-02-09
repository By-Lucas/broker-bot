import os
import sys
from pathlib import Path
from loguru import logger
from datetime import timedelta
from decouple import config, Csv

from django.contrib.messages import constants

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = "django-insecure-2$vxkgr8dn_b1v%3rx1!2dvbst#t*4l0^f2340&-m2#c2a=!=s"

DEBUG = True

ALLOWED_HOSTS = ["*"]


sys.path.append(os.path.join(BASE_DIR, 'apps'))

DJANGO_APPS = [
    'daphne',
    "channels",

    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

]

THIRD_APPS = [
    "rest_framework",
    'rest_framework.authtoken',
    "corsheaders",
    "widget_tweaks",
    "import_export",
    "django_celery_beat",
    "django_celery_results",
    'django_filters',
]

PROJECT_APPS = [
    #"accounts",
    "logs",
    "bots",
    "core",
    "trading",
    "callback",
    "customer",
    "quotexapi",
    "integrations",
    "notification",
]

INSTALLED_APPS = DJANGO_APPS + THIRD_APPS + PROJECT_APPS 


AUTH_USER_MODEL = 'customer.Customer'
LOGIN_URL = "customer:login"
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

MIDDLEWARE = [
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    #"logs.middleware.ExceptionLoggingMiddleware",

    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "broker_bot.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "broker_bot.wsgi.application"
ASGI_APPLICATION = "broker_bot.asgi.application"

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("redis", 6379)],  # Atualize para o endereço do Redis
        },
    },
}


# Database
# https://docs.djangoproject.com/en/5.0/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
LANGUAGE_CODE = 'pt-br'
TIME_ZONE = 'America/Sao_Paulo'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATIC_URL = '/static/'

STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'static'),
]

MEDIA_URL = "/media/"
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')


# TAGS MESSAGE TEMPLATE
MESSAGE_TAGS = {
    constants.DEBUG: 'primary',
    constants.ERROR: 'danger',
    constants.SUCCESS: 'success',
    constants.INFO: 'info',
    constants.WARNING: 'warning',
}


# RabbitMQ
RABBITMQ_USER = config("RABBITMQ_USER", default="guest")
RABBITMQ_PASSWORD = config("RABBITMQ_PASSWORD", default="guest")
RABBITMQ_HOST = config("RABBITMQ_HOST", default="rabbitmq")
RABBITMQ_PORT = config("RABBITMQ_PORT", default="5672")

CELERY_BROKER_URL = config(
    "CELERY_BROKER_URL",
    default=f"amqp://{RABBITMQ_USER}:{RABBITMQ_PASSWORD}@{RABBITMQ_HOST}:{RABBITMQ_PORT}//"
)

# Redis
REDIS_HOST = config("REDIS_HOST", default="redis")
REDIS_PORT = config("REDIS_PORT", default="6379")
CELERY_RESULT_BACKEND = config(
    "CELERY_RESULT_BACKEND",
    default=f"redis://{REDIS_HOST}:{REDIS_PORT}/0"
)

# Outras configurações Celery
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_TIMEZONE = "America/Sao_Paulo"
CELERY_TASK_TRACK_STARTED = True

# CONFIG E-MAIL
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'brokerbotshub@gmail.com'
EMAIL_HOST_PASSWORD = 'xrwv ythq ibaf bvxe'

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"
