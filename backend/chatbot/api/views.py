"""API views for the chatbot application.

Views stay thin: parse the request, call a service (services/), shape the
response. No document processing, retrieval, or LLM logic belongs here.

Endpoints
---------
GET  /api/health/                  — liveness + DB check
GET  /api/documents/?session_id=   — documents uploaded in one chat session
POST /api/documents/upload/        — upload a file (.pdf/.doc/.docx/.zip) to
                                     Supabase Storage and record metadata
                                     in PostgreSQL, associated with the
                                     session it was uploaded in
POST /api/chat/                    — save a question + a temporary answer
                                     in chat_messages (grouped by
                                     chat_sessions)

No preprocessing, retrieval or LLM logic belongs here.
"""
from __future__ import annotations

import os

from django.db import connection, transaction, OperationalError
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.views import APIView

from chatbot.api.serializers import (
    EXTENSION_CONTENT_TYPES,
    ChatMessageSerializer,
    ChatRequestSerializer,
    DocumentSerializer,
    DocumentSessionQuerySerializer,
    DocumentUploadSerializer,
)
from chatbot.models import ChatMessage, ChatSession, Document
from chatbot.services.storage import StorageError, StorageService


# ---------------------------------------------------------------------------
# Health
# ---------------------------------------------------------------------------

class HealthCheckView(APIView):
    """GET /api/health/ — verifies the backend is up and the DB is reachable."""

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request) -> Response:
        db_status = "ok"
        db_error: str | None = None

        try:
            connection.ensure_connection()
        except OperationalError as exc:
            db_status = "error"
            db_error = str(exc)

        payload: dict = {
            "status": "ok" if db_status == "ok" else "degraded",
            "service": "nexus-backend",
            "database": db_status,
        }
        if db_error:
            payload["database_error"] = db_error

        http_status = 200 if db_status == "ok" else 503
        return Response(payload, status=http_status)


# ---------------------------------------------------------------------------
# Document upload
# ---------------------------------------------------------------------------

class DocumentUploadView(APIView):
    """POST /api/documents/upload/

    Accepts ``multipart/form-data`` with:
        file       — .pdf / .doc / .docx / .zip (required, non-empty, ≤ 50 MB)
        source     — "university" | "student"
        session_id — chat_sessions id the file belongs to (optional: the very
                     first upload of a conversation may omit it, in which case
                     a new session is created and its id returned)

    Upload flow
    -----------
    1. Validate input (serializer) and resolve the chat session.
    2. Read file bytes into memory.
    3. Upload the original file to Supabase Storage → storage path.
    4. Create a Document record in PostgreSQL, linked to that session.
    5. Return the serialized document (including its ``session_id``).

    The file is stored as-is: no preprocessing happens in this step.
    Starting a new session never removes anything here — documents only ever
    change session when the client explicitly sends a different ``session_id``.

    If step 3 fails, nothing is written to the DB (consistent state).
    If step 4 fails after a successful upload, we attempt to delete the
    orphaned object from Storage and then surface the DB error to the caller.
    """

    authentication_classes: list = []
    permission_classes: list = []
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request) -> Response:
        # ------------------------------------------------------------------ #
        # 1. Validate request                                                  #
        # ------------------------------------------------------------------ #
        serializer = DocumentUploadSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        uploaded_file = serializer.validated_data["file"]
        source: str = serializer.validated_data["source"]
        original_name: str = uploaded_file.name
        requested_session_id = serializer.validated_data.get("session_id")

        # ------------------------------------------------------------------ #
        # 1b. Resolve the chat session this file belongs to                    #
        # ------------------------------------------------------------------ #
        # An unknown id is rejected before anything is written to Storage.
        # No id at all means this is the first upload of a conversation: the
        # session is opened together with the document record (step 4).
        session: ChatSession | None = None
        if requested_session_id is not None:
            session = ChatSession.objects.filter(pk=requested_session_id).first()
            if session is None:
                return Response(
                    {"detail": "Unknown chat session."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # ------------------------------------------------------------------ #
        # 2. Read bytes (we need them for the Storage upload)                  #
        # ------------------------------------------------------------------ #
        try:
            file_bytes: bytes = uploaded_file.read()
        except Exception as exc:
            return Response(
                {"detail": f"Failed to read uploaded file: {exc}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # ------------------------------------------------------------------ #
        # 3. Upload the original file to Supabase Storage                       #
        # ------------------------------------------------------------------ #
        # The extension decides the Content-Type sent to Storage so the bucket
        # sees the same value on every platform (see EXTENSION_CONTENT_TYPES).
        ext = os.path.splitext(original_name)[1].lower()
        content_type: str = (
            EXTENSION_CONTENT_TYPES.get(ext)
            or getattr(uploaded_file, "content_type", "")
            or "application/octet-stream"
        )

        try:
            storage = StorageService.from_settings()
            storage_path = storage.upload_file(
                file_bytes, original_name, source, content_type=content_type
            )
        except StorageError as exc:
            return Response(
                {"detail": str(exc)},
                status=status.HTTP_502_BAD_GATEWAY,
            )

        # ------------------------------------------------------------------ #
        # 4. Persist metadata in PostgreSQL (together with its session)         #
        # ------------------------------------------------------------------ #
        try:
            with transaction.atomic():
                if session is None:
                    # First upload of a conversation: open the chat session in
                    # the same transaction so a document is never saved
                    # without one. The id is handed back in the response.
                    session = ChatSession.objects.create()
                document = Document.objects.create(
                    title=original_name,          # human-readable display name
                    file_name=original_name,      # original filename for the response
                    file_path=storage_path,       # Supabase Storage key
                    source=source,
                    session=session,              # "My Documents" is session-scoped
                    status=Document.Status.UPLOADED,
                )
        except Exception as exc:
            # DB write failed after a successful Storage upload.
            # Attempt best-effort cleanup so we don't leave an orphan in Storage.
            try:
                storage.delete_object(storage_path)
            except StorageError:
                pass  # Log this in a real production system.
            return Response(
                {"detail": f"Document record could not be saved: {exc}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # ------------------------------------------------------------------ #
        # 5. Return the created document                                       #
        # ------------------------------------------------------------------ #
        response_serializer = DocumentSerializer(document)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)


# ---------------------------------------------------------------------------
# Document list (scoped to one chat session)
# ---------------------------------------------------------------------------

class DocumentListView(APIView):
    """GET /api/documents/?session_id=<uuid>

    Returns the documents uploaded during one chat session (newest first) —
    exactly what the "My Documents" sidebar renders.

    The list is deliberately scoped: session B never returns session A's
    files, and starting a new session deletes nothing, it simply opens a
    different session. ``session_id`` is required (400 when missing or
    malformed, 404 when it names a session that does not exist), so there is
    no endpoint that lists every document of every conversation.
    """

    authentication_classes: list = []
    permission_classes: list = []

    def get(self, request) -> Response:
        query = DocumentSessionQuerySerializer(data=request.query_params)
        if not query.is_valid():
            return Response(query.errors, status=status.HTTP_400_BAD_REQUEST)

        session_id = query.validated_data["session_id"]
        if not ChatSession.objects.filter(pk=session_id).exists():
            return Response(
                {"detail": "Unknown chat session."},
                status=status.HTTP_404_NOT_FOUND,
            )

        documents = Document.objects.filter(session_id=session_id)
        return Response(DocumentSerializer(documents, many=True).data)


# ---------------------------------------------------------------------------
# Ask question (temporary answer — no retrieval or LLM in this step)
# ---------------------------------------------------------------------------

class ChatView(APIView):
    """POST /api/chat/ — the temporary "Ask Question" endpoint.

    Persists both turns of the exchange, grouped by session::

        chat_sessions (1) ──* chat_messages (role: user, then assistant)

    Request
    -------
        {"question": "...", "session_id": "<uuid or null>"}

    Response (201)
    --------------
        {
          "session_id": "<uuid>",
          "session_title": "...",
          "messages": [ {user message}, {assistant message} ]
        }

    The assistant reply is a fixed placeholder produced by
    ``_temporary_reply()``: document processing, retrieval, embeddings and
    the LLM are intentionally not connected yet. The real pipeline replaces
    that helper later without changing this contract.
    """

    authentication_classes: list = []
    permission_classes: list = []

    def post(self, request) -> Response:
        # ------------------------------------------------------------------ #
        # 1. Validate input                                                    #
        # ------------------------------------------------------------------ #
        serializer = ChatRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        question: str = serializer.validated_data["question"].strip()
        session_id = serializer.validated_data.get("session_id")

        # ------------------------------------------------------------------ #
        # 2. Resolve the session (continue one, or start a new one)            #
        # ------------------------------------------------------------------ #
        existing = None
        if session_id is not None:
            existing = ChatSession.objects.filter(pk=session_id).first()
            if existing is None:
                return Response(
                    {"detail": "Unknown chat session."},
                    status=status.HTTP_404_NOT_FOUND,
                )

        # ------------------------------------------------------------------ #
        # 3. Save the question and the temporary answer together               #
        # ------------------------------------------------------------------ #
        with transaction.atomic():
            session = existing or ChatSession.objects.create(
                title=_session_title(question)
            )
            user_message = ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.USER,
                content=question,
            )
            assistant_message = ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.ASSISTANT,
                content=_temporary_reply(),
            )

        # ------------------------------------------------------------------ #
        # 4. Return the session id and both stored messages                    #
        # ------------------------------------------------------------------ #
        payload = {
            "session_id": str(session.id),
            "session_title": session.title,
            "messages": ChatMessageSerializer(
                [user_message, assistant_message], many=True
            ).data,
        }
        return Response(payload, status=status.HTTP_201_CREATED)


def _session_title(question: str, limit: int = 80) -> str:
    """Title for a new session: the first words of the opening question."""
    title = " ".join(question.split())
    if len(title) <= limit:
        return title
    return title[: limit - 1].rstrip() + "…"


def _temporary_reply() -> str:
    """Placeholder assistant answer used until the real pipeline exists.

    Deliberately states that no retrieval or language model is involved, so
    the response never pretends to have read the uploaded documents.
    """
    return (
        "Thanks — your question has been saved to this conversation.\n\n"
        "This is a temporary response: document processing, retrieval (RAG) "
        "and the language model are not connected yet, so I cannot answer "
        "from your documents in this step. Once they are wired in, this same "
        "endpoint will return a grounded answer with citations."
    )
