"""LLM configuration for the Nexus agent.

Responsibility: load credentials from the environment and return a configured
ChatGoogleGenerativeAI instance ready to be used by agent.py (or any other
service that needs the language model).

Usage::

    from chatbot.services.agent import ensure_llm_configured, get_llm

    ensure_llm_configured()   # raises LLMConfigError when misconfigured
    llm = get_llm()

Environment variables (defined in backend/.env):
    GEMINI_API_KEY  – Google AI API key (required, never hard-code).
    GEMINI_MODEL    – Gemini model id, e.g. "gemini-3.8-flash" (required).

Values are read from the process environment first, then (when the process
value is empty) straight from backend/.env. That second step matters because
``load_dotenv`` runs once at import: a dev server started *before* the key
was added would otherwise keep reporting the old empty value forever, and
editing backend/.env would appear to "do nothing".

There is deliberately **no fallback model and no fake answer**: when the key
is missing everywhere the configuration error is explicit (``LLMConfigError``)
and the Chat API reports it instead of pretending the model replied.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import dotenv_values, load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI

# Load backend/.env (anchored to this file, so it works from any cwd).
# `override=False` keeps any values already set in the process environment.
ENV_PATH = Path(__file__).resolve().parents[3] / ".env"
load_dotenv(ENV_PATH, override=False)


def _file_value(name: str) -> str:
    """Read one variable directly from backend/.env ("" when absent)."""
    try:
        return (dotenv_values(ENV_PATH).get(name) or "").strip()
    except OSError:
        return ""


def _setting(name: str) -> str:
    """Return ``name`` from the process env, falling back to backend/.env.

    Process values win (tests and CI can override them); the file is only
    consulted when the process value is empty, which is exactly the state a
    long-running dev server is stuck in after backend/.env is edited.
    """
    value = os.getenv(name, "").strip()
    return value if value else _file_value(name)


class LLMConfigError(ValueError):
    """The Gemini configuration is missing or empty.

    Subclasses ``ValueError`` so callers that historically caught
    ``ValueError`` from ``get_llm()`` keep working.
    """


def ensure_llm_configured() -> tuple[str, str]:
    """Validate the environment and return ``(api_key, model)``.

    Raises:
        LLMConfigError: with an actionable message naming the missing
            variable and the file to edit (backend/.env).
    """
    api_key = _setting("GEMINI_API_KEY")
    model = _setting("GEMINI_MODEL")

    if not api_key:
        raise LLMConfigError(
            "GEMINI_API_KEY is not set. Add it to backend/.env "
            "(GEMINI_API_KEY=...) before using the chat endpoint."
        )
    if not model:
        raise LLMConfigError(
            "GEMINI_MODEL is not set. Add it to backend/.env "
            "(e.g. GEMINI_MODEL=gemini-3.8-flash)."
        )
    return api_key, model


def get_llm() -> ChatGoogleGenerativeAI:
    """Return a configured Gemini LLM instance with ``temperature=0``.

    ``temperature=0`` keeps answers deterministic and reproducible, which a
    grounded, citation-based assistant needs.

    Raises:
        LLMConfigError: if ``GEMINI_API_KEY`` or ``GEMINI_MODEL`` is missing.
    """
    api_key, model = ensure_llm_configured()
    return ChatGoogleGenerativeAI(
        model=model,
        google_api_key=api_key,
        temperature=0,
        # Free-tier Gemini quotas are per-minute: retrying a 429 many times
        # (the library default) keeps the sliding window saturated and turns
        # one rate-limit blip into a permanent storm. Two attempts surface the
        # explicit quota error quickly instead of hanging for a minute.
        max_retries=2,
    )
