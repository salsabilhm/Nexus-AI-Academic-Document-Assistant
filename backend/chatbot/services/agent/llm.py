"""LLM configuration for the Nexus agent.

Responsibility: load credentials from the environment and return a configured
ChatGoogleGenerativeAI instance ready to be used by agent.py (or any other
service that needs the language model).

Usage::

    from .llm import get_llm

    llm = get_llm()         # raises ValueError if env vars are missing
    response = llm.invoke("Hello, Nexus!")

Environment variables (defined in backend/.env):
    GEMINI_API_KEY  – Google AI API key (required, never hard-code).
    GEMINI_MODEL    – Gemini model identifier, e.g. "gemini-1.5-flash" (required).
"""
from __future__ import annotations

import os

from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load variables from the project's .env file.
# `override=False` keeps any values already set in the process environment.
load_dotenv(override=False)


def get_llm() -> ChatGoogleGenerativeAI:
    """Return a configured Gemini LLM instance.

    Reads ``GEMINI_API_KEY`` and ``GEMINI_MODEL`` from the environment (populated
    by python-dotenv from backend/.env) and returns a
    :class:`~langchain_google_genai.ChatGoogleGenerativeAI` instance with
    ``temperature=0`` for deterministic, reproducible responses.

    Raises:
        ValueError: if either required environment variable is missing or empty.
    """
    api_key = os.getenv("GEMINI_API_KEY")
    model = os.getenv("GEMINI_MODEL")

    if not api_key:
        raise ValueError(
            "GEMINI_API_KEY is not set. "
            "Add it to backend/.env before starting the server."
        )
    if not model:
        raise ValueError(
            "GEMINI_MODEL is not set. "
            "Add it to backend/.env before starting the server."
        )

    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0,
    )
