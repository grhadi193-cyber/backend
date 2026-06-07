"""
Production settings.

Set DJANGO_SETTINGS_MODULE=config.settings.production on the server.
All secrets MUST be present in the environment — never hard-coded here.

Local "check" usage (Windows dev):
    python manage.py check --settings=config.settings.production
    → Works as long as .env contains at least placeholder values for
      SECRET_KEY, DATABASE_URL, ALLOWED_HOSTS, CORS_ALLOWED_ORIGINS.
"""
import os
import logging.handlers  # noqa: F401 — imported early so handlers dict is valid

import environ

from .base import (  # explicit imports — no star import — avoids mutation issues
    BASE_DIR,
    INSTALLED_APPS,
    MIDDLEWARE,
    ROOT_URLCONF,
    TEMPLATES,
    WSGI_APPLICATION,
    AUTH_USER_MODEL,
    AUTH_PASSWORD_VALIDATORS,
    LANGUAGE_CODE,
    TIME_ZONE,
    USE_I18N,
    USE_TZ,
    STATIC_URL,
    STATIC_ROOT,
    MEDIA_URL,
    MEDIA_ROOT,
    SIMPLE_JWT,
    OTP_EXPIRY_MINUTES,
    OTP_RATE_LIMIT_SECONDS,
    DEFAULT_PAGE_SIZE,
    MAX_PAGE_SIZE,
    KAVENEGAR_API_KEY,
    SMS_SENDER,
    PAYMENT_CALLBACK_BASE_URL,
    CORS_ALLOW_CREDENTIALS,
    DEFAULT_AUTO_FIELD,
    STATICFILES_STORAGE,
)

env = environ.Env()

_env_file = BASE_DIR / ".env"
if _env_file.exists():
    environ.Env.read_env(str(_env_file))

# ---------------------------------------------------------------------------
# Security
# ---------------------------------------------------------------------------
DEBUG = False

# On the production server these MUST be in the environment.
# On a dev machine running `check --settings=production` they fall back to
# safe placeholder values so the import succeeds without crashing.
SECRET_KEY = env("SECRET_KEY", default="placeholder-for-local-check-only-not-real")
ALLOWED_HOSTS = env.list("ALLOWED_HOSTS", default=["127.0.0.1", "localhost"])

# Warn loudly if someone accidentally deploys with the placeholder key.
if SECRET_KEY == "placeholder-for-local-check-only-not-real":
    import warnings
    warnings.warn(
        "SECRET_KEY is using the placeholder value — "
        "set a real SECRET_KEY in the environment before going live!",
        stacklevel=1,
    )

SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_HSTS_SECONDS = env.int("SECURE_HSTS_SECONDS", default=31536000)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# ---------------------------------------------------------------------------
# Database (PostgreSQL required in production)
# ---------------------------------------------------------------------------
DATABASES = {
    "default": env.db("DATABASE_URL", default="sqlite:///db.sqlite3"),
}
DATABASES["default"]["CONN_MAX_AGE"] = env.int("DB_CONN_MAX_AGE", default=60)

# Only add sslmode for non-SQLite backends to avoid sqlite3 warnings.
_db_url = env("DATABASE_URL", default="sqlite:///db.sqlite3")
if not _db_url.startswith("sqlite"):
    DATABASES["default"].setdefault("OPTIONS", {})
    DATABASES["default"]["OPTIONS"]["sslmode"] = env("DB_SSLMODE", default="prefer")

# ---------------------------------------------------------------------------
# Static files — WhiteNoise
# ---------------------------------------------------------------------------
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

# ---------------------------------------------------------------------------
# Email
# ---------------------------------------------------------------------------
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = env("EMAIL_HOST", default="localhost")
EMAIL_PORT = env.int("EMAIL_PORT", default=25)
EMAIL_USE_TLS = env.bool("EMAIL_USE_TLS", default=False)
EMAIL_HOST_USER = env("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD", default="")
DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@example.com")

# ---------------------------------------------------------------------------
# Payment gateway — redefine in full (do NOT mutate the base dict)
# ---------------------------------------------------------------------------
AZ_IRANIAN_BANK_GATEWAYS = {
    "BANKS": {
        "ZARINPAL": {
            "MERCHANT_CODE": env("ZARINPAL_MERCHANT_CODE", default=""),
            "SANDBOX": False,   # always OFF in production
        },
    },
    "IS_SAMPLE_FORM_ENABLE": False,
    "DEFAULT": "ZARINPAL",
}

# Production MUST have a real callback URL
PAYMENT_CALLBACK_BASE_URL = env("PAYMENT_CALLBACK_BASE_URL")
if not PAYMENT_CALLBACK_BASE_URL:
    raise ValueError("PAYMENT_CALLBACK_BASE_URL must be set in production environment")

# ---------------------------------------------------------------------------
# CORS
# ---------------------------------------------------------------------------
CORS_ALLOWED_ORIGINS = env.list(
    "CORS_ALLOWED_ORIGINS",
    default=[],
)

# ---------------------------------------------------------------------------
# Logging — rotating files + console
# ---------------------------------------------------------------------------
LOG_DIR = env("LOG_DIR", default=str(BASE_DIR / "logs"))
os.makedirs(LOG_DIR, exist_ok=True)

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {
            "format": "[{asctime}] {levelname} {name} pid={process:d} {message}",
            "style": "{",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "django.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "formatter": "verbose",
            "encoding": "utf-8",
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "filename": os.path.join(LOG_DIR, "django_errors.log"),
            "maxBytes": 10 * 1024 * 1024,
            "backupCount": 5,
            "level": "ERROR",
            "formatter": "verbose",
            "encoding": "utf-8",
        },
    },
    "root": {
        "handlers": ["console", "file"],
        "level": "WARNING",
    },
    "loggers": {
        "django": {
            "handlers": ["console", "file", "error_file"],
            "level": env("DJANGO_LOG_LEVEL", default="WARNING"),
            "propagate": False,
        },
        "django.db.backends": {
            "handlers": ["file"],
            "level": "WARNING",
            "propagate": False,
        },
        "django.security": {
            "handlers": ["error_file"],
            "level": "ERROR",
            "propagate": False,
        },
    },
}
