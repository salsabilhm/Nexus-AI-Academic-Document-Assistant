"""Vector store: pgvector inside the existing Supabase PostgreSQL database.

Two responsibilities (choreographed by ``rag/service.py``)::

    Embedding + Metadata  -> Vector Database      (`add`)
    Query Vector + Filters -> Similar Chunks      (`search`)

Implementation notes
--------------------
- Table ``document_vectors`` (chatbot.models.DocumentVector), column
  ``embedding vector(384)`` provided by the pgvector extension
  (migration 0003).
- All statements are raw SQL on Django's connection. The vector value is
  always passed as a JSON literal with an explicit ``::vector`` cast and the
  ``embedding`` column is never selected back (results carry content +
  metadata + score), so no client-side pgvector type registration is needed
  with psycopg 3.
- Similarity is cosine: distance operator ``<=>``, ``score = 1 - distance``
  (1.0 = identical direction, 0.0 = unrelated, -1.0 = opposite).
- ``add()`` first deletes the previous vectors of every document it receives,
  so re-indexing a document replaces its vectors instead of duplicating them.
- ``filters`` is a small allow-list mapped to real columns
  (document_type / document_id / session_id / chunk_id). An unknown filter
  raises ValueError: silently ignoring one would return wrong results.

Requires the Django app registry (models are imported for the table name);
only ``rag/embedder.py`` is usable outside a configured Django project.
"""
from __future__ import annotations

import json
import uuid
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

from django.db import connection
from django.utils import timezone

from chatbot.models import DocumentVector

_TABLE: str = DocumentVector._meta.db_table

# Public filter name -> column it maps to (see module docstring).
FILTERABLE_FIELDS: dict[str, str] = {
    "document_type": "document_type",
    "document_id": "document_id",
    "session_id": "session_id",
    "chunk_id": "chunk_id",
}

_INSERT_SQL = (
    f"INSERT INTO {_TABLE} "
    "(id, document_id, document_type, chunk_id, chunk_index, content, "
    " session_id, page, section, metadata, embedding, created_at) "
    "VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s::jsonb, %s::vector, %s)"
)


@dataclass
class VectorRecord:
    """One chunk ready to be written to the vector database.

    Built by ``RAGService.index`` from a ``ProcessedChunk``: the embedding
    plus every field retrieval needs for filtering and citation.
    """

    document_id: str
    chunk_id: str
    chunk_index: int
    content: str
    embedding: list[float]
    document_type: str = ""
    session_id: str | None = None
    page: int | None = None
    section: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class StoredChunk:
    """One search hit returned by ``VectorStore.search``."""

    content: str
    document_id: str
    document_type: str
    chunk_id: str
    chunk_index: int
    page: int | None
    section: str
    session_id: str | None
    score: float
    metadata: dict[str, Any] = field(default_factory=dict)


def _vector_literal(vector: Sequence[float]) -> str:
    """pgvector text literal, e.g. "[0.1,-0.2,...]" — cast to ::vector in SQL."""
    return json.dumps([float(value) for value in vector])


class VectorStore:
    """Read/write access to the pgvector index (no embedding logic here)."""

    # ------------------------------------------------------------------ #
    # Write: Embedding + Metadata -> Vector Database                      #
    # ------------------------------------------------------------------ #

    def add(self, records: Sequence[VectorRecord]) -> int:
        """Insert (or re-index) records; returns the number of vectors written.

        Existing vectors of the documents present in ``records`` are deleted
        first, making ``index()`` idempotent per document.
        """
        if not records:
            return 0

        document_ids = sorted({record.document_id for record in records})
        now = timezone.now()
        rows = [
            (
                uuid.uuid4(),
                record.document_id,
                record.document_type,
                record.chunk_id,
                record.chunk_index,
                record.content,
                record.session_id,
                record.page,
                record.section,
                json.dumps(record.metadata),
                _vector_literal(record.embedding),
                now,
            )
            for record in records
        ]

        with connection.cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {_TABLE} WHERE document_id = ANY(%s::uuid[])",
                [document_ids],
            )
            cursor.executemany(_INSERT_SQL, rows)
        return len(rows)

    def delete_for_document(self, document_id: str) -> int:
        """Remove every vector of one document (e.g. before re-processing)."""
        with connection.cursor() as cursor:
            cursor.execute(
                f"DELETE FROM {_TABLE} WHERE document_id = %s", [str(document_id)]
            )
            return cursor.rowcount

    # ------------------------------------------------------------------ #
    # Read: Query Vector + Filters -> Similar Chunks                      #
    # ------------------------------------------------------------------ #

    def search(
        self,
        vector: Sequence[float],
        filters: dict[str, Any] | None = None,
        top_k: int = 5,
    ) -> list[StoredChunk]:
        """Return the ``top_k`` most similar chunks, best score first.

        Raises ValueError for ``top_k < 1``, a zero vector (nothing sensible
        to compare against) or a filter outside ``FILTERABLE_FIELDS``.
        """
        if top_k < 1:
            raise ValueError(f"top_k must be >= 1, got {top_k}")
        if not vector or not any(vector):
            raise ValueError(
                "Cannot search with a zero vector (empty or stopword-only text)."
            )

        clauses: list[str] = []
        params: list[Any] = []
        for key, value in (filters or {}).items():
            column = FILTERABLE_FIELDS.get(key)
            if column is None:
                allowed = ", ".join(sorted(FILTERABLE_FIELDS))
                raise ValueError(
                    f"Unsupported filter {key!r}; allowed filters: {allowed}."
                )
            if value is None:
                clauses.append(f"{column} IS NULL")
            else:
                clauses.append(f"{column} = %s")
                params.append(value)

        where = f"WHERE {' AND '.join(clauses)}" if clauses else ""
        literal = _vector_literal(vector)
        sql = (
            "SELECT content, document_id, document_type, chunk_id, chunk_index, "
            "       page, section, session_id, metadata, "
            "       1 - (embedding <=> %s::vector) AS score "
            f"FROM {_TABLE} {where} "
            "ORDER BY embedding <=> %s::vector "
            "LIMIT %s"
        )
        # Parameter order follows the text order of the placeholders:
        # score expression, filters, ORDER BY expression, LIMIT.
        query_params = [literal, *params, literal, top_k]

        hits: list[StoredChunk] = []
        with connection.cursor() as cursor:
            cursor.execute(sql, query_params)
            columns = [column.name for column in cursor.description]
            for row in cursor.fetchall():
                record = dict(zip(columns, row))
                # jsonb comes back as a str on Django's psycopg cursors;
                # normalise so callers always get a dict.
                metadata = record["metadata"]
                if isinstance(metadata, str):
                    metadata = json.loads(metadata)
                hits.append(
                    StoredChunk(
                        content=record["content"],
                        document_id=str(record["document_id"]),
                        document_type=record["document_type"],
                        chunk_id=str(record["chunk_id"]),
                        chunk_index=record["chunk_index"],
                        page=record["page"],
                        section=record["section"],
                        session_id=(
                            str(record["session_id"]) if record["session_id"] else None
                        ),
                        score=float(record["score"]),
                        metadata=metadata or {},
                    )
                )
        return hits
