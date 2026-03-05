"""
AppConfig for the rag Django application.
"""

from django.apps import AppConfig


class RagConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "rag"
    verbose_name = "RAG Pipeline"
