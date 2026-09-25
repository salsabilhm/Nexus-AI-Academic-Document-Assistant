"""Root URL configuration for the Nexus API.

All API routes live under /api/ and are composed inside each app's api/urls.py,
so new endpoints can be added without touching this file.
"""
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    # App API routes
    path("api/", include("chatbot.api.urls")),
]
