"""Document orchestration service: uploaded file -> chunks -> vectors.

The single place that wires the processing pipeline together (the view
only triggers it; neither DocumentProcessor nor RAGService knows about
the others' internals)::

    uploaded bytes
        -> DocumentProcessor.process(file_path, document_id)   File -> ProcessedChunks
        -> DocumentChunk rows                                  text source of truth
        -> RAGService.index(processed_chunks)                  embeddings + metadata -> pgvector
        -> Document.status: uploaded -> processing -> ready | failed

Responsibilities kept here and nowhere else:
- write the uploaded bytes to a correctly-suffixed temporary file
  (the processor only accepts file paths);
- add the document-level metadata the processor cannot know
  (``document_type`` = documents.source, ``session_id``) before indexing,
  so retrieval can filter on them;
- persist chunks and index them in one transaction: either both exist or
  neither does;
- own the status transitions.

No background worker in this step: processing runs synchronously during
the upload request. A file that cannot be processed (.doc legacy binary,
PDF without extractable text, ...) ends as status="failed" — the stored
file itself is never removed by a processing failure.
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import TYPE_CHECKING

from django.db import transaction

from chatbot.models import Document, DocumentChunk
from chatbot.rag.service import RAGService
from chatbot.services.document_processor import DocumentProcessor

if TYPE_CHECKING:
    from chatbot.services.document_processor import ProcessedChunk

logger = logging.getLogger(__name__)


class DocumentService:
    """Runs preprocessing + RAG indexing for one uploaded document."""

    def __init__(
        self,
        processor: DocumentProcessor | None = None,
        rag_service: RAGService | None = None,
    ) -> None:
        self._processor = processor or DocumentProcessor()
        self._rag = rag_service or RAGService()

    def process_document(self, document: Document, file_bytes: bytes) -> list["ProcessedChunk"]:
        """Process ``file_bytes`` and index the resulting chunks.

        Returns the chunks on success; on failure the document is marked
        ``failed`` and the original exception is re-raised so the caller
        (the upload view) can log it — the upload contract itself is
        unchanged: 201 either way.
        """
        document.status = Document.Status.PROCESSING
        document.save(update_fields=["status", "updated_at"])

        suffix = Path(document.file_name).suffix.lower()
        temp_path: str | None = None
        try:
            # 1. File -> ProcessedChunks (no RAG knowledge inside the processor)
            with tempfile.NamedTemporaryFile(
                prefix="nexus_doc_", suffix=suffix, delete=False
            ) as tmp:
                tmp.write(file_bytes)
                temp_path = tmp.name

            chunks = self._processor.process(temp_path, str(document.id))
            if not chunks:
                raise ValueError(
                    f"{document.file_name}: processing produced no chunks."
                )

            # Document-level metadata for retrieval filters (see module docstring)
            for chunk in chunks:
                chunk.metadata["document_type"] = document.source
                chunk.metadata["session_id"] = (
                    str(document.session_id) if document.session_id else None
                )

            # 2. Persist the text and index it — one transaction, so the
            #    chunk rows and the vectors always agree.
            with transaction.atomic():
                DocumentChunk.objects.filter(document=document).delete()
                DocumentChunk.objects.bulk_create(
                    [DocumentChunk(**chunk.to_model_kwargs()) for chunk in chunks]
                )
                self._rag.index(chunks)

        except Exception:
            # Any failure (unreadable file, no extractable text, DB or
            # vector-store error) leaves the document in a terminal state:
            # stored but not retrievable. Re-raise for the caller to log.
            self._mark_failed(document)
            raise
        finally:
            if temp_path:
                try:
                    os.unlink(temp_path)
                except OSError:  # pragma: no cover - best effort cleanup
                    pass

        document.status = Document.Status.READY
        document.save(update_fields=["status", "updated_at"])
        return chunks

    @staticmethod
    def _mark_failed(document: Document) -> None:
        document.status = Document.Status.FAILED
        document.save(update_fields=["status", "updated_at"])
