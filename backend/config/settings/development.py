"""
Development settings for mr-insight project.

Usage:
    DJANGO_SETTINGS_MODULE=config.settings.development
"""

from .base import *  # noqa: F401, F403

DEBUG = True

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Show full error pages in development
INTERNAL_IPS = ["127.0.0.1"]
