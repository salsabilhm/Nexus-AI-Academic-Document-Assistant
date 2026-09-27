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
- Retrieval is precision-gated in three measured steps (never by guessing):
  1. a minimum cosine ``score`` in SQL (``RAG_SIMILARITY_THRESHOLD``,
     default :data:`DEFAULT_SIMILARITY_THRESHOLD`) — weak tail matches are
     dropped in the database and fewer than ``top_k`` rows may be returned;
  2. metadata-based suppression of *non-evidence* records — BibTeX
     entries, LaTeX class rules, Java method bodies, example assets and
     front/back-matter sections are not answers to content questions, and
     are kept only when the query itself asks about that kind of content
     (see ``_suppress_non_evidence``);
  3. deduplication of identical rows (same ``chunk_id`` or same text).
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Iterable, Mapping

from .embedder import Embedder, content_terms
from .vector_store import StoredChunk, VectorRecord, VectorStore

if TYPE_CHECKING:  # typing only: chatbot.rag stays importable without pypdf
    from chatbot.services.document_processor import ProcessedChunk


# Minimum cosine score a chunk must reach to be returned. Calibrated on the
# real corpus (2026-09 measurements with the hashing embedder): every chunk
# that genuinely answers a query scored >= 0.05, while the sub-0.03 band held
# only hash-noise tail. The score cannot separate in-domain noise (a template
# placeholder can out-score real content), which is what the metadata gate in
# ``_suppress_non_evidence`` handles — the floor here is deliberately low so
# no legitimate evidence (glued-text PDF chunks included) is ever cut.
DEFAULT_SIMILARITY_THRESHOLD = 0.03

# Environment variable that overrides the default (a number in [-1, 1],
# or "off" to disable the floor entirely). Read per call so a changed
# value applies without re-importing the module.
SIMILARITY_THRESHOLD_ENV = "RAG_SIMILARITY_THRESHOLD"

# retrieve() asks the store for more candidates than the caller wants, so
# the metadata gate has headroom: after suppression the best top_k survivors
# are still returned (or fewer — never padded with weak matches).
_OVERFETCH_FACTOR = 3
_MIN_CANDIDATES = 15

_UNSET = object()  # distinguishes "use the environment" from min_score=None

# --- query domains ------------------------------------------------------- #
# A suppressed record (see _ancillary_kind) becomes eligible again when the
# query itself talks about that kind of content: asking about references
# must retrieve the bibliography, asking about margins must retrieve the
# class file. EN/FR terms, already accent-normalized by content_terms().

_CITATION_TERMS = frozenset({
    "citation", "citations", "bibliography", "bibliographie", "reference",
    "references", "referenced", "cited", "cite", "author", "authors",
    "bibtex", "doi",
})
_FORMATTING_TERMS = frozenset({
    "format", "formats", "formatting", "formatage", "margin", "margins",
    "font", "fonts", "spacing", "layout", "style", "styles", "cls",
})
_CODE_TERMS = frozenset({
    "code", "java", "class", "classes", "method", "methods", "function",
    "functions", "program", "programs", "programming", "programmation",
    "algorithm", "algorithms",
})
_ASSET_TERMS = frozenset({
    "example", "examples", "exemple", "exemples", "sample", "samples",
    "listing", "listings", "table", "tables", "figure", "figures",
    "illustration", "illustrations",
    "algorithm", "algorithms", "algorithme", "algorithmes",
    "pseudocode", "pseudocodes",
})
_BACK_MATTER_TERMS = frozenset({
    "dedication", "dedications", "dedicate", "acknowledgment",
    "acknowledgments", "acknowledgements", "acknowledgement",
    "remerciement", "remerciements",
})

# Directories inside a ZIP that hold sample/scaffolding assets rather than
# document content (spec: "chapters/contributions.tex must remain
# distinguishable from bibliography.bib and listings/A.java"). "algorithms"
# joins the set after the live E2E leaked algorithms/example.tex into a
# structure answer.
_ASSET_DIRECTORIES = frozenset({"tables", "listings", "figures", "images",
                                "assets", "examples", "algorithms"})

# section values that are front/back matter: present in the document, but
# not an answer to a content question about its subject or structure.
_BACK_MATTER_SECTIONS = frozenset({"dedication", "bibliography",
                                   "acknowledgments", "acknowledgements"})

# Which query domain re-enables which suppressed record kind. A placeholder
# image has no text to answer with, so it is never evidence.
_UNLOCK_TERMS: dict[str, frozenset[str]] = {
    "citation": _CITATION_TERMS,
    "formatting": _FORMATTING_TERMS,
    "code": _CODE_TERMS,
    "example_asset": _ASSET_TERMS,
    "back_matter": _CITATION_TERMS | _BACK_MATTER_TERMS,
    "image_placeholder": frozenset(),
}


def _ancillary_kind(hit: StoredChunk) -> str | None:
    """Classify a chunk that is *not* document content, or ``None``.

    Purely metadata-driven — the text is never rewritten or dropped at
    index time, so a citation/class/code chunk stays fully retrievable for
    the queries that actually target it (see ``_UNLOCK_TERMS``).
    """
    metadata = hit.metadata
    file_type = str(metadata.get("file_type") or "").lower()

    # An image without OCR is stored as a status note, not evidence.
    if file_type == "image" and metadata.get("ocr_status") != "extracted":
        return "image_placeholder"

    if file_type == "bib" or metadata.get("citation_key") or metadata.get("entry_type"):
        return "citation"
    if file_type == "cls" or metadata.get("rule_type"):
        return "formatting"
    if file_type == "java" or metadata.get("content_type") in {"method", "class_declaration"}:
        return "code"

    source = str(metadata.get("source_file") or "").replace("\\", "/").lower()
    directory = source.split("/", 1)[0] if "/" in source else ""
    if directory in _ASSET_DIRECTORIES:
        return "example_asset"

    section = str(hit.section or "").strip().lower()
    if section in _BACK_MATTER_SECTIONS:
        return "back_matter"
    return None


def _suppress_non_evidence(query: str, hits: list[StoredChunk]) -> list[StoredChunk]:
    """Drop records that cannot answer ``query`` — unless the query asks
    for that kind of content (bibliography questions keep .bib entries).

    Only *ancillary* records are ever suppressed; ordinary content chunks
    are never dropped for "weak relevance" — with the hashing embedder a
    legitimate chunk (glued-text PDF, paraphrase) can score lower than a
    placeholder, so text-level gating would starve real evidence. The
    false-positive tail of content chunks is bounded by top_k and judged
    by the LLM against the grounded-answering rules.
    """
    terms = content_terms(query)
    kept: list[StoredChunk] = []
    for hit in hits:
        kind = _ancillary_kind(hit)
        if kind is None or (terms & _UNLOCK_TERMS[kind]):
            kept.append(hit)
    return kept


def _deduplicate(hits: list[StoredChunk]) -> list[StoredChunk]:
    """First occurrence wins: same chunk_id, or byte-identical text.

    Only true duplicates are removed — two *different* chunks of the same
    document remain (they are distinct evidence, e.g. two pages).
    """
    seen_ids: set[str] = set()
    seen_text: set[str] = set()
    unique: list[StoredChunk] = []
    for hit in hits:
        if hit.chunk_id in seen_ids:
            continue
        normalized = " ".join(hit.content.split())
        if normalized and normalized in seen_text:
            continue
        seen_ids.add(hit.chunk_id)
        if normalized:
            seen_text.add(normalized)
        unique.append(hit)
    return unique


def _configured_threshold() -> float | None:
    """Resolve ``RAG_SIMILARITY_THRESHOLD`` -> floor value or ``None``.

    Unset/empty -> :data:`DEFAULT_SIMILARITY_THRESHOLD`; ``"off"`` (or
    ``"none"``/``"disabled"``) -> no floor; anything else must parse to a
    cosine value in [-1, 1] — a typo raises instead of silently disabling
    relevance filtering (explicit configuration, never fake success).
    """
    raw = os.environ.get(SIMILARITY_THRESHOLD_ENV, "").strip()
    if not raw:
        return DEFAULT_SIMILARITY_THRESHOLD
    lowered = raw.lower()
    if lowered in {"off", "none", "disabled"}:
        return None
    try:
        value = float(raw)
    except ValueError:
        raise ValueError(
            f"{SIMILARITY_THRESHOLD_ENV} must be a number in [-1, 1], or "
            f"'off' to disable (got {raw!r})."
        ) from None
    if not -1.0 <= value <= 1.0:
        raise ValueError(
            f"{SIMILARITY_THRESHOLD_ENV} must be within [-1, 1] "
            f"(cosine score range), got {value!r}."
        )
    return value


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
        min_score: Any = _UNSET,
    ) -> list[RetrievedChunk]:
        """Return up to ``top_k`` chunks most relevant to ``query``.

        The question is only embedded temporarily for the similarity search;
        it is never written to the vector database (see store.search, which
        performs a single SELECT). ``filters`` restricts the search by
        metadata, e.g. ``{"document_type": "university"}``.

        Relevance pipeline (result may be **shorter** than ``top_k``):
        1. SQL floor — ``min_score`` if given, else ``RAG_SIMILARITY_THRESHOLD``
           (default :data:`DEFAULT_SIMILARITY_THRESHOLD`, ``"off"`` disables);
           the store is asked for ``top_k * 3`` (min 15) candidates so the
           gate below has headroom;
        2. metadata gate — non-evidence records (bib/class/java/example
           assets/front-back matter) are suppressed unless the query asks
           for that content (``_suppress_non_evidence``);
        3. dedup (``chunk_id`` or identical text) and a final cut to
           ``top_k``, preserving score-descending order.

        An empty/blank query — or one that embeds to the zero vector (only
        stopwords) — returns ``[]`` instead of meaningless results.
        ``min_score=None`` explicitly disables the score floor; a value
        outside [-1, 1] raises ValueError.
        """
        if top_k < 1:
            raise ValueError(f"top_k must be >= 1, got {top_k}")
        if not query or not query.strip():
            return []

        if min_score is _UNSET:
            threshold = _configured_threshold()
        else:
            threshold = min_score
            if threshold is not None and not -1.0 <= float(threshold) <= 1.0:
                raise ValueError(
                    f"min_score must be within [-1, 1] (cosine score range), "
                    f"got {threshold!r}"
                )

        query_vector = self._embedder.embed(query)
        if not any(query_vector):
            return []

        candidates = max(top_k * _OVERFETCH_FACTOR, _MIN_CANDIDATES)
        hits = self._store.search(
            query_vector,
            filters=dict(filters or {}),
            top_k=candidates,
            min_score=threshold,
        )
        hits = _deduplicate(_suppress_non_evidence(query, hits))
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
            for hit in hits[:top_k]
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
