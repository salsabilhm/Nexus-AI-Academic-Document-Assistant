"""URL routes for the chatbot API.

Mounted under /api/ in config/urls.py. Add new endpoints here — one line per
route — so the root URL configuration never has to change.
"""
from django.urls import path

from . import views

app_name = "chatbot"

urlpatterns = [
    path("health/", views.HealthCheckView.as_view(), name="health"),
    # TODO: path("documents/", ...), path("chat/", ...), ...
]
