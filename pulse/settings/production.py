import os

from .base import *  # noqa: F401,F403

SECRET_KEY = os.environ.get("SECRET_KEY")
DEBUG = False
ALLOWED_HOSTS = [os.environ.get("ALLOWED_HOST", "")]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME"),
        "USER": os.environ.get("DB_USER"),
        "PASSWORD": os.environ.get("DB_PASSWORD"),
        "HOST": os.environ.get("DB_HOST"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}
