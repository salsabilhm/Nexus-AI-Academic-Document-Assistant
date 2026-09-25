"""Retrieval (RAG) service.

Responsibility: given a user question, find the most relevant document chunks.

Future pipeline (not implemented yet):
    embed query -> search vector store -> re-rank -> return passages with sources

TODO:
- choose and integrate a vector store later (none is connected today);
- embed chunks produced by DocumentProcessor;
- retrieve top-k passages for a query and return their source metadata;
- keep this layer free of HTTP concerns and of prompt/agent decisions.

The LLM itself is not called here: RAG only retrieves context.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class RetrievedPassage:
    """A passage retrieved for a query, with the information needed to cite it."""

    text: str
    document_id: str
    document_name: str
    metadata: dict[str, Any] = field(default_factory=dict)
    score: float = 0.0


class RagService:
    """Retrieves relevant passages for a question. Implementation comes later."""

    def retrieve(self, query: str, top_k: int = 5) -> list[RetrievedPassage]:
        """Return the passages most relevant to `query`.

        TODO: implement embedding + similarity search once a vector store exists.
        """
        raise NotImplementedError(
            "RagService.retrieve is a skeleton; retrieval is not implemented yet."
        )
