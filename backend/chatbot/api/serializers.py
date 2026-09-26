"""Serializers for the chatbot API.

DocumentUploadSerializer  — validates the multipart upload request
                            (file + source + session_id).
DocumentSerializer        — shapes a Document model instance into the
                            API response payload.
DocumentSessionQuerySerializer
                          — validates GET /api/documents/?session_id=…
ChatRequestSerializer     — validates an Ask Question request
                            (question + optional session_id).
ChatMessageSerializer     — shapes a ChatMessage for the chat response.
"""
from __future__ import annotations

import os

from rest_framework import serializers

from chatbot.models import ChatMessage, Document

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALLOWED_SOURCES = [choice[0] for choice in Document.Source.choices]
MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024  # 50 MB hard limit

# --- Upload types supported by the MVP ------------------------------------
# Documents are stored as-is: no preprocessing happens in this step.
ALLOWED_EXTENSIONS = (".pdf", ".doc", ".docx", ".zip")

# Content type sent to Supabase Storage for each supported extension.
# Written out explicitly (instead of mimetypes.guess_type) so the value is
# identical on every platform — Windows resolves several of these from the
# registry and may return a type the bucket refuses.
EXTENSION_CONTENT_TYPES: dict[str, str] = {
    ".pdf": "application/pdf",
    ".doc": "application/msword",
    ".docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ".zip": "application/zip",
}

# MIME types a browser may report for the same files. Used only as a fallback
# for uploads that carry no extension; the extension stays the primary gate.
ALLOWED_MIME_TYPES = frozenset(EXTENSION_CONTENT_TYPES.values()) | {
    "application/x-zip-compressed",
}


# ---------------------------------------------------------------------------
# Upload input serializer
# ---------------------------------------------------------------------------

class DocumentUploadSerializer(serializers.Serializer):
    """Validates the multipart/form-data POST body for document uploads.

    Fields
    ------
    file       : .pdf / .doc / .docx / .zip file (required, non-empty, ≤ 50 MB)
    source     : "university" or "student"
    session_id : chat_sessions id the file belongs to. Omit it on the very
                 first upload of a conversation — the view then opens a new
                 session and returns its id, which the client keeps for every
                 following request.
    """

    file = serializers.FileField(
        required=True,
        help_text="File to upload (.pdf, .doc, .docx or .zip).",
    )
    source = serializers.ChoiceField(
        choices=ALLOWED_SOURCES,
        required=True,
        help_text='"university" or "student".',
    )
    session_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="chat_sessions id the document is uploaded in; "
                  "omit to start a new session.",
    )

    # ------------------------------------------------------------------
    # Field-level validation
    # ------------------------------------------------------------------

    def validate_file(self, value):
        """Enforce the supported file types and the size limits.

        The extension is the primary check: browsers freely mis-report MIME
        types for .doc/.zip, so a file is accepted only when its extension is
        in ``ALLOWED_EXTENSIONS`` — or when it has no extension at all and
        carries an exactly-known MIME type.
        """
        name: str = value.name or ""
        ext = os.path.splitext(name)[1].lower()
        content_type: str = (getattr(value, "content_type", "") or "").lower()

        if ext not in ALLOWED_EXTENSIONS:
            bare_mime = content_type.split(";")[0].strip()
            if not (ext == "" and bare_mime in ALLOWED_MIME_TYPES):
                allowed = ", ".join(ALLOWED_EXTENSIONS)
                raise serializers.ValidationError(
                    f"Unsupported file type — allowed extensions: {allowed}. "
                    f"Received content type: {content_type!r}, filename: {name!r}."
                )

        if value.size == 0:
            raise serializers.ValidationError("The uploaded file is empty.")

        if value.size > MAX_FILE_SIZE_BYTES:
            limit_mb = MAX_FILE_SIZE_BYTES // (1024 * 1024)
            raise serializers.ValidationError(
                f"File size exceeds the {limit_mb} MB limit "
                f"({value.size / (1024 * 1024):.1f} MB received)."
            )

        return value


# ---------------------------------------------------------------------------
# Response serializer
# ---------------------------------------------------------------------------

class DocumentSerializer(serializers.ModelSerializer):
    """Read-only representation of a Document returned to the frontend.

    Intentionally omits internal fields (file_path, updated_at) that the
    client does not need and that could expose storage implementation details.

    ``session_id`` is the chat session the file was uploaded in — the client
    adopts it as its current session when the very first upload opened one.
    """

    # Return the original filename the user uploaded, not the internal title.
    name = serializers.CharField(source="file_name")
    # Maps to documents.session_id (the raw foreign key value on the model).
    session_id = serializers.UUIDField(
        read_only=True,
        help_text="chat_sessions id the document belongs to.",
    )

    class Meta:
        model = Document
        fields = ["id", "name", "source", "status", "created_at", "session_id"]
        read_only_fields = fields


# ---------------------------------------------------------------------------
# Document list query serializer
# ---------------------------------------------------------------------------

class DocumentSessionQuerySerializer(serializers.Serializer):
    """Validates GET /api/documents/?session_id=<uuid>.

    The sidebar is scoped to a single conversation, so the session must be
    named explicitly — there is deliberately no "list every document" call.
    """

    session_id = serializers.UUIDField(
        required=True,
        help_text="chat_sessions id whose documents should be returned.",
    )


# ---------------------------------------------------------------------------
# Chat input serializer
# ---------------------------------------------------------------------------

class ChatRequestSerializer(serializers.Serializer):
    """Validates POST /api/chat/ — the temporary "Ask Question" endpoint.

    Fields
    ------
    question   : the user's question (required, non-empty, ≤ 4000 chars).
    session_id : an existing ``chat_sessions`` id. Omit it (or send null) to
                 start a new session; send the value returned by a previous
                 request to keep grouping messages in the same session.
    """

    question = serializers.CharField(
        required=True,
        allow_blank=False,
        trim_whitespace=True,
        max_length=4000,
        help_text="The user's question.",
    )
    session_id = serializers.UUIDField(
        required=False,
        allow_null=True,
        help_text="chat_sessions id to continue; omit to start a new session.",
    )


# ---------------------------------------------------------------------------
# Chat response serializer
# ---------------------------------------------------------------------------

class ChatMessageSerializer(serializers.ModelSerializer):
    """Shapes a saved ChatMessage for the POST /api/chat/ response."""

    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "created_at"]
        read_only_fields = fields
