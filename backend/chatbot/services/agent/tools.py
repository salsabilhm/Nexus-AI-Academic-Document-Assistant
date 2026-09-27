"""LangChain tools for the Nexus agent.

Responsibility: expose the RAG layer (``chatbot.rag``) to the agent as a
callable tool. This module never talks to pgvector, the vector store or the
embedder directly — it only calls ``RAGService.retrieve()``, the same public
API the rest of the backend uses (see ``chatbot/rag/service.py``).

Usage::

    from chatbot.services.agent.tools import search_documents, make_search_documents

    text = search_documents.invoke({"query": "methodology", "source": "student"})

    # Scoped to one chat session (what ask_nexus does):
    scoped = make_search_documents(session_id="<uuid>")

``session_id`` is an *injected* tool argument: it never appears in the JSON
schema the LLM sees (the model only chooses ``query`` and ``source``), so a
conversation can only retrieve evidence from its own session and the model
cannot hallucinate a UUID.
"""
from __future__ import annotations

from typing import Annotated, Any, Literal

from langchain_core.tools import BaseTool, InjectedToolArg, tool

from chatbot.rag.service import RAGService, RetrievedChunk

# How many chunks one retrieval returns: enough context for a grounded,
# citable answer without flooding the model's context window.
RAG_TOP_K = 5

Source = Literal["university", "student", "both"]

# One shared, stateless RAG service for the whole process — the tool only
# needs retrieve(); indexing stays in DocumentService.
_rag = RAGService()


def _format_chunk(chunk: RetrievedChunk) -> str:
    """Render one retrieved chunk as a citation block for the LLM.

    Includes everything needed for grounded citations (document id, type,
    page, section, source file, relevance score) without inventing any
    value: fields the extractor could not detect are simply omitted.
    """
    parts = [f"document_id: {chunk.document_id}", f"type: {chunk.document_type}"]
    if chunk.page is not None:
        parts.append(f"page: {chunk.page}")
    if chunk.section:
        parts.append(f"section: {chunk.section}")
    source_file = chunk.metadata.get("source_file")
    if source_file:
        parts.append(f"source_file: {source_file}")
    file_type = chunk.metadata.get("file_type")
    if file_type:
        # Original format (pdf/tex/bib/java/...): lets the model tell a PDF
        # requirement page from a LaTeX template chapter when citing.
        parts.append(f"file_type: {file_type}")
    parts.append(f"score: {chunk.score:.3f}")
    return f"[{' | '.join(parts)}]\n{chunk.text}"


def make_search_documents(session_id: str | None = None) -> BaseTool:
    """Build the ``search_documents`` tool, optionally scoped to one session.

    Args:
        session_id: The chat session the agent is answering in. When given,
            retrieval is filtered to documents uploaded in that session
            (``document_vectors.session_id``); the argument is injected, not
            chosen by the LLM. ``None`` searches across all documents.

    Returns:
        A LangChain tool whose structured output is
        ``(text_for_the_llm, list[RetrievedChunk])`` — the chunks ride along
        as the tool *artifact* so the API can return them as sources.
    """

    @tool(response_format="content_and_artifact")
    def search_documents(
        query: str,
        source: Source = "both",
        session_id: Annotated[str | None, InjectedToolArg] = session_id,
    ) -> tuple[str, list[RetrievedChunk]]:
        """Search the uploaded academic documents for evidence.

        Args:
            query: The question or topic to search for, in the user's words.
            source: Which collection to search: ``"university"`` for
                institutional guidelines/requirements, ``"student"`` for
                uploaded student work, ``"both"`` (default) for everything.
        """
        filters: dict[str, Any] = {}
        if source != "both":
            # Pushed down to SQL (document_type is an allow-listed column in
            # the vector store) — never retrieve-then-filter in Python.
            filters["document_type"] = source
        if session_id:
            filters["session_id"] = str(session_id)

        results = _rag.retrieve(
            query=query, filters=filters or None, top_k=RAG_TOP_K
        )

        if not results:
            where = f" in the '{source}' collection" if source != "both" else ""
            return (
                f"No relevant documents found for query '{query}'{where}. "
                "There is insufficient evidence to answer — say so explicitly. "
                "Tell the user the available documents do not contain this "
                "information — do not guess or fill the gap.",
                [],
            )

        return "\n\n---\n\n".join(_format_chunk(c) for c in results), results

    return search_documents


# Default (unscoped) tool, importable as chatbot.services.agent.tools.search_documents.
search_documents: BaseTool = make_search_documents()
