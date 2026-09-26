"""LangChain tools for the Nexus agent.

Responsibility: wrap the RAG service as callable LangChain tools so that the
agent can invoke document search during a conversation.

Usage::

    from .tools import search_documents

    results = search_documents.invoke({"query": "methodology", "source": "student"})
"""
from __future__ import annotations

from typing import Literal

from langchain_core.tools import tool

from ..rag import RagService, RetrievedPassage

# A single shared RagService instance — stateless today, ready to be replaced
# with a fully wired implementation once a vector store is connected.
_rag = RagService()

Source = Literal["university", "student", "both"]


def _format_passage(passage: RetrievedPassage) -> str:
    """Render a single retrieved passage as a plain-text block."""
    return (
        f"[{passage.document_name}]\n"
        f"{passage.text}\n"
        f"(score: {passage.score:.3f})"
    )


@tool
def search_documents(query: str, source: Source = "both") -> str:
    """Search academic documents in the knowledge base.

    Args:
        query:  The question or topic to search for.
        source: Which document collection to search.
                ``"university"`` — institutional guidelines and requirements only.
                ``"student"``    — uploaded student documents only (theses, drafts…).
                ``"both"``       — search across all available documents (default).

    Returns:
        A formatted string with the relevant passages and their sources, or a
        message stating that no results were found.
    """
    passages: list[RetrievedPassage] = _rag.retrieve(query)

    if source != "both":
        passages = [
            p for p in passages
            if p.metadata.get("source") == source
        ]

    if not passages:
        return (
            f"No relevant documents found for query '{query}'"
            + (f" in the '{source}' collection." if source != "both" else ".")
        )

    blocks = [_format_passage(p) for p in passages]
    return "\n\n---\n\n".join(blocks)
