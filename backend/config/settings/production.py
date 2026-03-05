"""
Production settings for mr-insight project.

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.production
"""

from decouple import config

from .base import *  # noqa: F401, F403

DEBUG = False

# In production, SECRET_KEY must be set via environment variable.
SECRET_KEY = config("SECRET_KEY")

# Security hardening
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = "DENY"
SECURE_SSL_REDIRECT = config("SECURE_SSL_REDIRECT", default=True, cast=bool)
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
