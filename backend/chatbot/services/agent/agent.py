"""Nexus agent — entry point for conversational document assistance.

Responsibility: assemble the LLM, the document-search tool and the system
prompt into a runnable LangChain agent, and expose ``ask_nexus()``, the one
helper callers (the Chat API) use to get a grounded answer.

Usage::

    from chatbot.services.agent import ask_nexus

    result = ask_nexus("What is the methodology of my thesis?", session_id=sid)
    result.answer    # grounded text
    result.sources   # the RetrievedChunks that support it

The agent decides on its own when to call ``search_documents``; callers do
not manage tool dispatch. Conversation memory comes from
``state_memory.get_messages_for_agent()`` — retrieved chunks are *never*
stored as chat history (RAG evidence stays retrieval context for the
current answer only).
"""
from __future__ import annotations

from dataclasses import dataclass, field

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from chatbot.rag.service import RetrievedChunk

from .llm import get_llm
from .prompts import SYSTEM_PROMPT
from .state_memory import get_messages_for_agent
from .tools import make_search_documents


@dataclass
class AgentResult:
    """One answer plus the evidence retrieved for it.

    Successor of the old ``services/agent.AgentResult``: same idea — an
    answer and the chunks that support it — with ``sources`` naming what the
    Chat API now returns.
    """

    answer: str
    sources: list[RetrievedChunk] = field(default_factory=list)


def create_nexus_agent(session_id: str | None = None) -> CompiledStateGraph:
    """Build and return a configured Nexus agent graph.

    Wires together:
    - the Gemini LLM (environment variables via :func:`~.llm.get_llm`),
    - the ``search_documents`` tool scoped to ``session_id``,
    - :data:`~.prompts.SYSTEM_PROMPT` (grounded-answer rules).

    Args:
        session_id: Chat session to scope document retrieval to.

    Returns:
        A compiled LangGraph state-graph ready to be invoked.

    Raises:
        LLMConfigError: if ``GEMINI_API_KEY`` / ``GEMINI_MODEL`` are missing.
    """
    return create_agent(
        model=get_llm(),
        tools=[make_search_documents(session_id)],
        system_prompt=SYSTEM_PROMPT,
    )


def ask_nexus(question: str, session_id: str | None = None) -> AgentResult:
    """Run the agent on ``question`` and return answer + retrieved evidence.

    Conversation context: the stored history of ``session_id`` (loaded via
    ``state_memory``) plus the current question. The Chat API persists the
    user turn *before* calling us, so the question is only appended when it
    is not already the last stored message — it is never sent twice.

    The agent may call ``search_documents`` zero or more times; every chunk
    it retrieves is returned in ``sources`` (deduplicated by ``chunk_id``,
    order of first retrieval).

    Args:
        question: The user's natural-language question.
        session_id: Chat session providing history and retrieval scope.

    Returns:
        :class:`AgentResult` with the final text and the retrieved chunks.

    Raises:
        LLMConfigError: if the LLM environment configuration is missing.
        RuntimeError: if the agent produces no assistant message.
    """
    agent = create_nexus_agent(session_id)

    messages: list[BaseMessage] = (
        list(get_messages_for_agent(session_id)) if session_id else []
    )
    if not messages or not (
        isinstance(messages[-1], HumanMessage) and messages[-1].content == question
    ):
        messages.append(HumanMessage(content=question))

    result: dict = agent.invoke({"messages": messages})
    return AgentResult(
        answer=_final_answer(result.get("messages", [])),
        sources=_collected_sources(result.get("messages", [])),
    )


def _final_answer(messages: list[BaseMessage]) -> str:
    """Text of the last AI message (str or Gemini content-block list)."""
    for message in reversed(messages):
        if isinstance(message, AIMessage):
            content = message.content
            if isinstance(content, str):
                return content.strip()
            if isinstance(content, list):  # content blocks, e.g. [{"text": ...}]
                parts = [
                    block.get("text", "")
                    for block in content
                    if isinstance(block, dict)
                ]
                return "".join(parts).strip()
            return str(content).strip()
    raise RuntimeError("The agent returned no assistant message.")


def _collected_sources(messages: list[BaseMessage]) -> list[RetrievedChunk]:
    """Every chunk the tool retrieved during this run, deduplicated."""
    sources: list[RetrievedChunk] = []
    seen: set[str] = set()
    for message in messages:
        if not isinstance(message, ToolMessage):
            continue
        for chunk in message.artifact or ():
            if chunk.chunk_id in seen:
                continue
            seen.add(chunk.chunk_id)
            sources.append(chunk)
    return sources
