"""
URL configuration for mr_insight_backend project.
"""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("rag.urls")),
]
