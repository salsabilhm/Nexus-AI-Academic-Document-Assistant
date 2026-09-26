"""Models for the chatbot application.

Django is the source of truth for the database schema. Run
``python manage.py migrate`` whenever models change.

Tables created:
  documents         — uploaded file metadata (linked to the session it was
                      uploaded in via documents.session_id)
  document_chunks   — text chunks extracted from a document
  document_vectors  — embedded chunks in pgvector (retrieval index, see
                      chatbot/rag/; embedding vector(384) + metadata)
  chat_sessions     — one conversation per session
  chat_messages     — individual turns inside a session
"""
import uuid

from django.db import models
from pgvector.django import VectorField

from chatbot.rag.embedder import DEFAULT_DIMENSION


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


class DocumentVector(models.Model):
    """One embedded chunk stored in the pgvector retrieval index.

    Written exclusively through ``chatbot.rag`` (RAGService.index ->
    VectorStore, raw SQL); this model exists so Django owns the schema —
    migration 0003 also enables the ``vector`` extension. One row per
    indexed chunk:

        embedding   vector(384) — output of chatbot.rag.embedder.Embedder
                                  (DEFAULT_DIMENSION; changing it means a
                                  migration + full re-index)
        metadata    document_type / session / page / section are promoted
                    to columns so retrieval can filter them; the remaining
                    processor metadata (source_file, heading, char_count,
                    ...) stays in the JSON column.

    Deleting a document cascades to its vectors; deleting a chat session
    only detaches them (SET_NULL), mirroring documents.session.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    document = models.ForeignKey(
        Document, on_delete=models.CASCADE, related_name="vectors"
    )
    chunk_id = models.UUIDField(
        help_text="ProcessedChunk.chunk_id (same id as document_chunks.id)."
    )
    chunk_index = models.PositiveIntegerField()
    document_type = models.CharField(
        max_length=20,
        blank=True,
        default="",
        help_text='Document.Source: "university" or "student" — lets retrieval filter by type.',
    )
    session = models.ForeignKey(
        "ChatSession",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="vectors",
        help_text="Chat session the document was uploaded in (null for legacy documents).",
    )
    page = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Source page when the extractor could detect one.",
    )
    section = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Section/heading the chunk came from (shown in citations).",
    )
    content = models.TextField(
        help_text="Chunk text, so retrieval can return it without a second lookup."
    )
    embedding = VectorField(dimensions=DEFAULT_DIMENSION)
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Processor metadata not promoted to a column.",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "document_vectors"
        indexes = [
            models.Index(fields=["document_type"], name="dv_document_type_idx"),
        ]

    def __str__(self) -> str:
        return f"Vector {self.chunk_index} of {self.document_id}"


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
