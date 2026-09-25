"""Agent / workflow orchestration service.

Responsibility: decide which operation runs for a request and in which order —
e.g. "is this a document comparison, a simple retrieval question, or a chat
answer?". The agent coordinates services; it does not contain their logic.

Future behaviour (not implemented yet):
    classify request -> pick tools (document_processor / rag / llm) -> run
    workflow -> assemble answer + sources

TODO:
- define the supported operations and their preconditions;
- implement a small decision loop that calls DocumentProcessor, RagService and
  the LLM layer through well-defined interfaces;
- always return the sources used for an answer so the API can show them;
- keep LLM credentials inside the LLM layer, never here or in the frontend.
"""
from __future__ import annotations

from dataclasses import dataclass, field

from .rag import RetrievedPassage


@dataclass
class AgentResult:
    """Outcome of a workflow run: the answer and the passages that support it."""

    answer: str
    passages: list[RetrievedPassage] = field(default_factory=list)
    operation: str = ""


class Agent:
    """Chooses and runs the workflow for a request. Implementation comes later."""

    def run(self, question: str) -> AgentResult:
        """Route a request to the right tools and build the response.

        TODO: implement the decision loop once RAG and the LLM layer exist.
        """
        raise NotImplementedError(
            "Agent.run is a skeleton; the agent workflow is not implemented yet."
        )
