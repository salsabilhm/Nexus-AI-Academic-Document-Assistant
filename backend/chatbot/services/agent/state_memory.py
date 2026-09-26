"""Conversation memory bridge between Django/PostgreSQL and the LangChain agent.

Responsibility: read and write chat history using the existing Django ORM
models (``ChatSession``, ``ChatMessage``) and convert that history into
LangChain message objects that the agent can consume directly.

This module deliberately contains NO LLM, NO agent, NO RAG, and NO pgvector
logic. It is the sole bridge between the database and the agent's message list.

Usage::

    from .state_memory import (
        get_conversation_history,
        save_user_message,
        save_assistant_message,
        get_messages_for_agent,
    )
"""
from __future__ import annotations

import uuid

from langchain_core.messages import AIMessage, BaseMessage, HumanMessage

from ...models import ChatMessage


def get_conversation_history(session_id: uuid.UUID | str) -> list[ChatMessage]:
    """Return all messages for a session, ordered chronologically.

    Queries ``chat_messages`` filtered by the given session and sorted by
    ``created_at`` ascending so that the returned list reflects the real
    conversation order (oldest first).

    Args:
        session_id: The UUID of the ``ChatSession``.

    Returns:
        A list of :class:`~chatbot.models.ChatMessage` instances, oldest first.
        Returns an empty list when the session has no messages yet.
    """
    return list(
        ChatMessage.objects.filter(session_id=session_id).order_by("created_at")
    )


def save_user_message(session_id: uuid.UUID | str, content: str) -> ChatMessage:
    """Persist a user turn to the database.

    Creates a new ``ChatMessage`` row with ``role=USER`` associated with the
    given session. The ``created_at`` timestamp is set automatically by Django.

    Args:
        session_id: The UUID of the ``ChatSession`` this message belongs to.
        content:    The user's message text.

    Returns:
        The newly created :class:`~chatbot.models.ChatMessage` instance.
    """
    return ChatMessage.objects.create(
        session_id=session_id,
        role=ChatMessage.Role.USER,
        content=content,
    )


def save_assistant_message(
    session_id: uuid.UUID | str, content: str
) -> ChatMessage:
    """Persist an assistant reply to the database.

    Creates a new ``ChatMessage`` row with ``role=ASSISTANT`` associated with
    the given session. The ``created_at`` timestamp is set automatically by
    Django.

    Args:
        session_id: The UUID of the ``ChatSession`` this message belongs to.
        content:    The assistant's reply text.

    Returns:
        The newly created :class:`~chatbot.models.ChatMessage` instance.
    """
    return ChatMessage.objects.create(
        session_id=session_id,
        role=ChatMessage.Role.ASSISTANT,
        content=content,
    )


def get_messages_for_agent(
    session_id: uuid.UUID | str,
) -> list[BaseMessage]:
    """Return the session's conversation history as LangChain message objects.

    Loads the full message history via :func:`get_conversation_history` and
    converts each row to the matching LangChain type:

    - ``ChatMessage.Role.USER``      → :class:`~langchain_core.messages.HumanMessage`
    - ``ChatMessage.Role.ASSISTANT`` → :class:`~langchain_core.messages.AIMessage`

    The resulting list can be passed directly to the agent as the ``messages``
    key of its input state, giving it full awareness of the prior conversation.

    Args:
        session_id: The UUID of the ``ChatSession``.

    Returns:
        A list of :class:`~langchain_core.messages.BaseMessage` instances
        (``HumanMessage`` or ``AIMessage``), oldest first.
        Returns an empty list when the session has no history.
    """
    history = get_conversation_history(session_id)

    messages: list[BaseMessage] = []
    for msg in history:
        if msg.role == ChatMessage.Role.USER:
            messages.append(HumanMessage(content=msg.content))
        elif msg.role == ChatMessage.Role.ASSISTANT:
            messages.append(AIMessage(content=msg.content))
        # Any unexpected role value is silently skipped — future-proofing only.

    return messages
