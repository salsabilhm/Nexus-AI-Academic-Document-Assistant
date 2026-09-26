"""Models for the chatbot application.

Django is the source of truth for the database schema. Run
``python manage.py migrate`` whenever models change.

Tables created:
  documents         — uploaded file metadata (linked to the session it was
                      uploaded in via documents.session_id)
  document_chunks   — text chunks extracted from a document
  chat_sessions     — one conversation per session
  chat_messages     — individual turns inside a session
"""
import uuid

from django.db import models


class Document(models.Model):
    """Metadata for an uploaded document (PDF, DOCX, …).

    Every document remembers the chat session it was uploaded in, so the
    "My Documents" sidebar can show only the files belonging to the
    conversation currently open. Sessions are never deleted when a user
    starts a new one: the file and its row stay in storage/PostgreSQL and
    are simply shown again when that session is reopened.
    """

    class Source(models.TextChoices):
        UNIVERSITY = "university", "University"
        STUDENT = "student", "Student"

    class Status(models.TextChoices):
        UPLOADED = "uploaded", "Uploaded"
        PROCESSING = "processing", "Processing"
        READY = "ready", "Ready"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    file_name = models.CharField(max_length=255)
    file_path = models.TextField()
    source = models.CharField(max_length=20, choices=Source.choices)
    # Chat session this file was uploaded in. Null only for documents that
    # pre-date session tracking; new uploads always carry a session.
    session = models.ForeignKey(
        "ChatSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="documents",
        help_text="Chat session the document was uploaded in.",
    )
    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.UPLOADED
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "documents"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.title} ({self.source})"


class DocumentChunk(models.Model):
    """A text excerpt extracted from a Document, ready for embedding."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="chunks"
    )
    chunk_index = models.PositiveIntegerField()
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "document_chunks"
        ordering = ["document", "chunk_index"]

    def __str__(self) -> str:
        return f"Chunk {self.chunk_index} of {self.document_id}"


class ChatSession(models.Model):
    """A single conversation thread."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "chat_sessions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"Session {self.id}"


class ChatMessage(models.Model):
    """One turn (user or assistant) inside a ChatSession."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(
        ChatSession, on_delete=models.CASCADE, related_name="messages"
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "chat_messages"
        ordering = ["session", "created_at"]

    def __str__(self) -> str:
        return f"[{self.role}] {self.content[:60]}"
