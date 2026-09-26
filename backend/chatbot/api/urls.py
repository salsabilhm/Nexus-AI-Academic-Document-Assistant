"""URL routes for the chatbot API.

Mounted under /api/ in config/urls.py. Add new endpoints here — one line per
route — so the root URL configuration never has to change.

Current routes
--------------
GET  health/                — liveness + DB check
GET  documents/             — documents of one session (?session_id=<uuid>)
POST documents/upload/      — upload a file (multipart/form-data: file + source
                              + session_id)
POST chat/                  — save a question + a temporary answer
"""
from django.urls import path

from . import views

app_name = "chatbot"

urlpatterns = [
    path("health/", views.HealthCheckView.as_view(), name="health"),
    path(
        "documents/upload/",
        views.DocumentUploadView.as_view(),
        name="document-upload",
    ),
    path("documents/", views.DocumentListView.as_view(), name="document-list"),
    path("chat/", views.ChatView.as_view(), name="chat"),
]
