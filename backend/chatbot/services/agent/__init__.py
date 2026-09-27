"""Nexus agent package — LLM + tools + prompts + conversation memory.

Public surface (what the rest of the backend imports)::

    from chatbot.services.agent import (
        AgentResult, ask_nexus, create_nexus_agent,   # agent entry points
        search_documents, make_search_documents,      # RAG tool
        get_messages_for_agent,                       # chat history -> messages
        LLMConfigError, ensure_llm_configured,        # explicit LLM config
        get_llm, SYSTEM_PROMPT,
    )

This package replaces the old ``services/agent.py`` skeleton: there is now
exactly one ``chatbot.services.agent`` (a package, no competing module).
"""
from .agent import AgentResult, ask_nexus, create_nexus_agent
from .llm import LLMConfigError, ensure_llm_configured, get_llm
from .prompts import SYSTEM_PROMPT
from .state_memory import (
    get_conversation_history,
    get_messages_for_agent,
    save_assistant_message,
    save_user_message,
)
from .tools import make_search_documents, search_documents

__all__ = [
    "AgentResult",
    "SYSTEM_PROMPT",
    "LLMConfigError",
    "ask_nexus",
    "create_nexus_agent",
    "ensure_llm_configured",
    "get_conversation_history",
    "get_llm",
    "get_messages_for_agent",
    "make_search_documents",
    "save_assistant_message",
    "save_user_message",
    "search_documents",
]
