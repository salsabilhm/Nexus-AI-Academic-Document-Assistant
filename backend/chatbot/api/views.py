"""API views for the chatbot application.

Views stay thin: parse the request, call a service (services/), shape the
response. No document processing, retrieval, or LLM logic belongs here.
"""
from rest_framework.response import Response
from rest_framework.views import APIView


class HealthCheckView(APIView):
    """GET /api/health/ — verifies that the frontend can reach the backend."""

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request) -> Response:
        return Response({"status": "ok", "service": "nexus-backend"})


# TODO(document endpoints): add upload/list/delete document views here once
# DocumentProcessor exists (POST /api/documents/, GET /api/documents/, ...).

# TODO(chat endpoints): add the chat view here once the agent exists
# (POST /api/chat/ returning the answer and its sources).
