import os

from dotenv import load_dotenv

from .base import *  # noqa: F401,F403

load_dotenv()

SECRET_KEY = os.environ.get("SECRET_KEY", "default-dev-key")
DEBUG = True
ALLOWED_HOSTS = ["*"]

if os.environ.get("DB_ENGINE", "sqlite").lower() == "postgres":
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": os.environ.get("DB_NAME", "pulse_db"),
            "USER": os.environ.get("DB_USER", "pulse_user"),
            "PASSWORD": os.environ.get("DB_PASSWORD", "pulse_password"),
            "HOST": os.environ.get("DB_HOST", "localhost"),
            "PORT": os.environ.get("DB_PORT", "5432"),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",  # noqa: F405
        }
    }
