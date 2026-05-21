"""
Local development settings (Windows / Linux workstation).
"""
from .base import *  # noqa: F401, F403

DEBUG = True

ALLOWED_HOSTS = ["*"]

# ── Static files ────────────────────────────────────────────
# روی local با DEBUG=True خود Django staticfiles را serve میکند.
# WhiteNoise را از middleware برمیداریم تا با Swagger/Admin تداخل نداشته باشد.
MIDDLEWARE = [m for m in MIDDLEWARE if "whitenoise" not in m.lower()]  # noqa: F405

# از storage پیشفرض Django استفاده میکنیم (نه CompressedManifest)
STATICFILES_STORAGE = "django.contrib.staticfiles.storage.StaticFilesStorage"

# ── Database ─────────────────────────────────────────────────
# DATABASE_URL=sqlite:///db.sqlite3  در .env تنظیم شده

# ── django-debug-toolbar ─────────────────────────────────────
try:
    import debug_toolbar  # noqa: F401
    INSTALLED_APPS += ["debug_toolbar"]  # noqa: F405
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]
except ImportError:
    pass

# ── Logging ──────────────────────────────────────────────────
LOGGING["loggers"]["django"]["level"] = "DEBUG"  # noqa: F405

# ── Email ────────────────────────────────────────────────────
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
