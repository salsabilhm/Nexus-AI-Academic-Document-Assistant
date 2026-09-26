"""Nexus agent — entry point for conversational document assistance.

Responsibility: assemble the LLM, the document search tool, and the system
prompt into a runnable LangChain agent; expose a simple ``ask_nexus`` helper
that callers use to get an answer from the agent.

Usage::

    from .agent import ask_nexus

    answer = ask_nexus("What is the research methodology in my thesis?")

The agent decides on its own when to call ``search_documents``; callers do not
need to manage tool dispatch.
"""
from __future__ import annotations

from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph

from .llm import get_llm
from .prompts import SYSTEM_PROMPT
from .tools import search_documents


def create_nexus_agent() -> CompiledStateGraph:
    """Build and return a configured Nexus agent graph.

    Wires together:
    - the Gemini LLM (loaded from environment variables via :func:`get_llm`),
    - the :func:`~tools.search_documents` tool for RAG-backed document retrieval,
    - the :data:`~prompts.SYSTEM_PROMPT` that defines Nexus's behaviour.

    Returns:
        A compiled LangGraph state-graph ready to be invoked.

    Raises:
        ValueError: if required environment variables (``GEMINI_API_KEY``,
            ``GEMINI_MODEL``) are missing.
    """
    return create_agent(
        model=get_llm(),
        tools=[search_documents],
        system_prompt=SYSTEM_PROMPT,
    )


def ask_nexus(question: str) -> str:
    """Invoke the Nexus agent with a user question and return its answer.

    Creates a fresh agent for each call (stateless — no cross-call memory).
    The agent uses the ``search_documents`` tool whenever the question may be
    answered by the available academic documents.

    Args:
        question: The user's natural-language question.

    Returns:
        The agent's final text response.

    Raises:
        ValueError: if LLM environment variables are missing.
        RuntimeError: if the agent produces no response messages.
    """
    agent = create_nexus_agent()
    result: dict = agent.invoke({"messages": [HumanMessage(content=question)]})

    messages = result.get("messages", [])
    if not messages:
        raise RuntimeError("The agent returned no messages.")

    return str(messages[-1].content)
