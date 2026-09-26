"""RAG service — the two functions of the retrieval pipeline.

::

    index():    DocumentProcessor.process -> ProcessedChunks
                    -> RAGService.index()
                    -> Embedder (text -> vector)
                    -> VectorStore (vectors + metadata -> pgvector)

    retrieve(): User Question -> Agent -> RAG tool
                    -> RAGService.retrieve()
                    -> Embedder (question -> query vector, temporary)
                    -> VectorStore (similarity search + metadata filters)
                    -> relevant chunks (content + sources metadata)

Rules this module obeys
-----------------------
- It never parses files: chunks arrive from the orchestration layer
  (``chatbot.services.document_service``), which calls ``DocumentProcessor``
  first and this service after — RAG logic stays out of the processor.
- ``retrieve()`` never writes: the question is embedded only to be compared
  against the indexed chunks and is not stored anywhere ("do NOT index the
  question").
- It decides no workflow and generates no text: the Agent/LLM layer will
  turn the returned chunks into an answer with citations. This layer only
  retrieves context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Mapping

from .embedder import Embedder
from .vector_store import VectorRecord, VectorStore

if TYPE_CHECKING:  # typing only: chatbot.rag stays importable without pypdf
    from chatbot.services.document_processor import ProcessedChunk


@dataclass
class RetrievedChunk:
    """One relevant chunk with everything needed for sources/citations.

    Mirrors the metadata stored at index time: ``document_id``,
    ``document_type`` (university | student), ``page`` / ``section`` when the
    extractor could detect them, ``session_id``, plus ``score`` (cosine
    similarity in [-1, 1], higher = more similar) and the full processor
    ``metadata`` (source_file, file_type, heading, ...).
    """

    text: str
    document_id: str
    document_type: str
    chunk_id: str
    chunk_index: int
    page: int | None = None
    section: str = ""
    session_id: str | None = None
    score: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)


class RAGService:
    """``index(chunks)`` and ``retrieve(query, filters, top_k)`` — nothing else."""

    def __init__(
        self,
        embedder: Embedder | None = None,
        store: VectorStore | None = None,
    ) -> None:
        # Both collaborators are injectable so tests can pass fakes and a
        # future API-backed embedder can replace Embedder without touching
        # this class.
        self._embedder = embedder or Embedder()
        self._store = store or VectorStore()

    @property
    def embedder(self) -> Embedder:
        return self._embedder

    # ------------------------------------------------------------------ #
    # index(): ProcessedChunks -> vectors + metadata in the Vector DB      #
    # ------------------------------------------------------------------ #

    def index(self, chunks: Iterable["ProcessedChunk"]) -> int:
        """Embed every chunk and store it with its metadata.

        Expects the chunk ``metadata`` to already carry the document-level
        fields used for filtering (``document_type``, ``session_id``) — the
        orchestration layer adds them before calling, since only it knows
        the Document. Returns the number of vectors written.
        """
        records = [self._to_record(chunk) for chunk in chunks]
        return self._store.add(records)

    # ------------------------------------------------------------------ #
    # retrieve(): question -> relevant chunks (nothing is written)          #
    # ------------------------------------------------------------------ #

    def retrieve(
        self,
        query: str,
        filters: Mapping[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[RetrievedChunk]:
        """Return the ``top_k`` chunks most relevant to ``query``.

        The question is only embedded temporarily for the similarity search;
        it is never written to the vector database (see store.search, which
        performs a single SELECT). ``filters`` restricts the search by
        metadata, e.g. ``{"document_type": "university"}``.

        An empty/blank query — or one that embeds to the zero vector (only
        stopwords) — returns ``[]`` instead of meaningless results.
        """
        if top_k < 1:
            raise ValueError(f"top_k must be >= 1, got {top_k}")
        if not query or not query.strip():
            return []

        query_vector = self._embedder.embed(query)
        if not any(query_vector):
            return []

        hits = self._store.search(query_vector, filters=dict(filters or {}), top_k=top_k)
        return [
            RetrievedChunk(
                text=hit.content,
                document_id=hit.document_id,
                document_type=hit.document_type,
                chunk_id=hit.chunk_id,
                chunk_index=hit.chunk_index,
                page=hit.page,
                section=hit.section,
                session_id=hit.session_id,
                score=hit.score,
                metadata=hit.metadata,
            )
            for hit in hits
        ]

    # ------------------------------------------------------------------ #
    # Helpers                                                              #
    # ------------------------------------------------------------------ #

    def _to_record(self, chunk: "ProcessedChunk") -> VectorRecord:
        """ProcessedChunk -> VectorRecord (embedding included)."""
        metadata = dict(getattr(chunk, "metadata", None) or {})
        raw_session = metadata.get("session_id")
        return VectorRecord(
            document_id=str(chunk.document_id),
            chunk_id=str(chunk.chunk_id),
            chunk_index=int(chunk.chunk_index),
            content=str(chunk.text),
            embedding=self._embedder.embed(chunk.text),
            document_type=str(metadata.get("document_type") or ""),
            session_id=str(raw_session) if raw_session else None,
            page=_as_page(metadata.get("page")),
            section=str(metadata.get("section") or metadata.get("heading") or ""),
            metadata=metadata,
        )


def _as_page(value: Any) -> int | None:
    """Best-effort int page number; anything unusable becomes None."""
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, str) and value.strip().isdigit():
        return int(value.strip())
    return None
