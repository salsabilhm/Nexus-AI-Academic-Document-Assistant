"""Tests for the Nexus agent package (chatbot/services/agent/) and its API.

Levels (mirrors tests_rag.py):
    PackageSurfaceTests / LLMConfigTests / PromptRulesTests / SearchToolTests
        — pure Python (SimpleTestCase), no database.
    AskNexusTests / StateMemoryTests / ChatEndpointTests / SourcesPayloadTests
        — ORM and HTTP (TestCase) against the test database.

What is covered:
    - the public import surface and the "one agent only" rule (package, no
      competing services/agent.py module);
    - explicit LLM configuration errors (no fake success when the key is
      missing);
    - the grounded-answering rules in the system prompt;
    - search_documents: hidden session_id, server-side filters, top_k,
      citation blocks, artifact with the retrieved chunks;
    - ask_nexus: history loading, question de-duplication, source dedup;
    - POST /api/chat/: contract (session_id, session_title, messages) plus
      the additive answer + sources, 404/400/502/503 and rollback on error.

Run: python manage.py test chatbot --keepdb
"""
from __future__ import annotations

import ast
import os
import uuid
from pathlib import Path
from unittest import mock

from django.test import SimpleTestCase, TestCase
from django.urls import reverse
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

import chatbot.services.agent as agent_package
from chatbot.api import views as views_module
from chatbot.models import ChatMessage, ChatSession, Document
from chatbot.rag.service import RetrievedChunk
from chatbot.services.agent import (
    SYSTEM_PROMPT,
    AgentResult,
    LLMConfigError,
    ask_nexus,
    ensure_llm_configured,
    get_llm,
    get_messages_for_agent,
    make_search_documents,
    search_documents,
)
from chatbot.services.agent import agent as agent_module
from chatbot.services.agent import llm as llm_module
from chatbot.services.agent import tools as tools_module


def make_chunk(**overrides) -> RetrievedChunk:
    """A RetrievedChunk shaped exactly like RAGService.retrieve() returns."""
    values: dict = {
        "text": "The methodology follows a two-stage evaluation protocol.",
        "document_id": str(uuid.uuid4()),
        "document_type": "student",
        "chunk_id": str(uuid.uuid4()),
        "chunk_index": 0,
        "page": 3,
        "section": "2. Methodology",
        "session_id": None,
        "score": 0.87654321,
        "metadata": {"source_file": "thesis.pdf"},
    }
    values.update(overrides)
    return RetrievedChunk(**values)


# ---------------------------------------------------------------------------
# Package surface
# ---------------------------------------------------------------------------


class PackageSurfaceTests(SimpleTestCase):
    """The public names exist and there is exactly one agent implementation."""

    def test_public_names_are_importable(self) -> None:
        for name in (
            "AgentResult",
            "ask_nexus",
            "create_nexus_agent",
            "search_documents",
            "make_search_documents",
            "get_messages_for_agent",
            "get_conversation_history",
            "save_user_message",
            "save_assistant_message",
            "LLMConfigError",
            "ensure_llm_configured",
            "get_llm",
            "SYSTEM_PROMPT",
        ):
            self.assertTrue(hasattr(agent_package, name), name)
        self.assertIn("search_documents", agent_package.__all__)

    def test_single_agent_implementation(self) -> None:
        # chatbot.services.agent must be the package; the old competing
        # chatbot/services/agent.py module must not exist anymore.
        package_dir = Path(agent_package.__file__).resolve().parent
        self.assertEqual(package_dir.name, "agent")
        self.assertTrue((package_dir / "agent.py").exists())  # agent/agent.py
        self.assertFalse((package_dir.parent / "agent.py").exists())  # no module

    def test_state_memory_is_pure_db_to_messages_bridge(self) -> None:
        # state_memory must not pull in pgvector, RAG, the LLM or the agent:
        # it only maps ChatSession/ChatMessage rows to LangChain messages.
        source = (Path(agent_package.__file__).resolve().parent
                  / "state_memory.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        imported: set[str] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                imported.update(alias.name for alias in node.names)
            elif isinstance(node, ast.ImportFrom):
                if node.level:  # relative import: record the module tail
                    imported.add("." * node.level + (node.module or ""))
                elif node.module:
                    imported.add(node.module)

        for module in imported:
            self.assertFalse(module.startswith("chatbot.rag"), module)
            self.assertFalse(module.startswith("langchain_google_genai"), module)
            self.assertNotIn("pgvector", module)
            self.assertNotIn("tools", module)
            self.assertNotIn("langchain.agents", module)
        # The only project dependency is the Django model layer (relative
        # "from ...models import ChatMessage" -> recorded as "...models").
        self.assertIn("...models", imported)
        self.assertNotIn("os.getenv", source)
        self.assertNotIn("GEMINI", source)

    def test_agent_result_shape(self) -> None:
        result = AgentResult(answer="grounded")
        self.assertEqual(result.answer, "grounded")
        self.assertEqual(result.sources, [])
        chunk = make_chunk()
        with_sources = AgentResult(answer="x", sources=[chunk])
        self.assertEqual(with_sources.sources, [chunk])


# ---------------------------------------------------------------------------
# LLM configuration (explicit errors, never a fake success)
# ---------------------------------------------------------------------------


class LLMConfigTests(SimpleTestCase):
    """GEMINI_API_KEY / GEMINI_MODEL are validated, never hard-code."""

    def test_missing_api_key_raises_explicit_error(self) -> None:
        # Patch the .env-file fallback too: the developer's own backend/.env
        # may contain a real key, and this test simulates a *missing* one.
        with mock.patch.dict(
            os.environ, {"GEMINI_API_KEY": "", "GEMINI_MODEL": "gemini-3.8-flash"}
        ), mock.patch.object(llm_module, "_file_value", return_value=""):
            with self.assertRaises(LLMConfigError) as ctx:
                ensure_llm_configured()
        message = str(ctx.exception)
        self.assertIn("GEMINI_API_KEY", message)
        self.assertIn("backend/.env", message)

    def test_missing_model_raises_explicit_error(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key",
                                          "GEMINI_MODEL": ""}), \
                mock.patch.object(llm_module, "_file_value", return_value=""):
            with self.assertRaises(LLMConfigError) as ctx:
                ensure_llm_configured()
        message = str(ctx.exception)
        self.assertIn("GEMINI_MODEL", message)
        self.assertIn("backend/.env", message)

    def test_llm_config_error_is_a_value_error(self) -> None:
        # Callers that historically caught ValueError keep working.
        self.assertTrue(issubclass(LLMConfigError, ValueError))

    def test_get_llm_returns_deterministic_model(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "test-key",
                                          "GEMINI_MODEL": "gemini-3.8-flash"}):
            llm = get_llm()
        self.assertEqual(getattr(llm, "temperature", None), 0)
        # Fail fast on quota errors instead of retry-storming a 429 window.
        self.assertEqual(getattr(llm, "max_retries", None), 2)

    def test_get_llm_refuses_unconfigured_environment(self) -> None:
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "",
                                          "GEMINI_MODEL": ""}), \
                mock.patch.object(llm_module, "_file_value", return_value=""):
            with self.assertRaises(LLMConfigError):
                get_llm()

    def test_stale_process_env_falls_back_to_env_file(self) -> None:
        # Regression: a dev server started with `--noreload` before the key
        # was added keeps an empty value in os.environ. Reading backend/.env
        # on demand means editing the file works without a server restart.
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "",
                                          "GEMINI_MODEL": ""}), \
                mock.patch.object(
                    llm_module,
                    "_file_value",
                    side_effect=lambda name: {
                        "GEMINI_API_KEY": "AQ.file-key",
                        "GEMINI_MODEL": "gemini-3.8-flash",
                    }[name],
                ):
            api_key, model = ensure_llm_configured()
        self.assertEqual(api_key, "AQ.file-key")
        self.assertEqual(model, "gemini-3.8-flash")

    def test_process_env_wins_over_env_file(self) -> None:
        # Real process values (tests, CI secrets) must not be overridden.
        with mock.patch.dict(os.environ, {"GEMINI_API_KEY": "AQ.process-key",
                                          "GEMINI_MODEL": "gemini-3.8-flash"}), \
                mock.patch.object(
                    llm_module, "_file_value", return_value="AQ.file-key"
                ):
            api_key, model = ensure_llm_configured()
        self.assertEqual(api_key, "AQ.process-key")
        self.assertEqual(model, "gemini-3.8-flash")


# ---------------------------------------------------------------------------
# System prompt: the 9 grounded-answering rules
# ---------------------------------------------------------------------------


class PromptRulesTests(SimpleTestCase):
    """Every rule the Chat API contract promises is in the system prompt."""

    REQUIRED_FRAGMENTS = [
        # 1. the LLM decides to use the tool for document questions
        "You decide when a search is needed",
        # 1b. never answer a document question unsearched
        "Never answer a document question without searching",
        # 2. retrieved content is the truth
        "only source of truth",
        # 3. no invented requirements/citations/facts
        "Do not invent requirements, facts, statistics",
        "Never construct or guess a citation",
        # 4. explicit "not enough information"
        "state explicitly that the available documents do not provide enough",
        # 5. comparisons retrieve both sides first
        "retrieve evidence for BOTH sides first",
        # 6. university vs student is always distinguished
        "label which side each statement comes from",
        '"university requirements" vs "student content"',
        # 7. sources are included
        "indicate the document, page or section",
        # 9. pgvector/embedding internals stay hidden
        "Never expose internal implementation details",
    ]

    def test_all_grounded_rules_present(self) -> None:
        for fragment in self.REQUIRED_FRAGMENTS:
            self.assertIn(fragment, SYSTEM_PROMPT, fragment)

    def test_prompt_names_the_tool_and_its_source_argument(self) -> None:
        self.assertIn("`search_documents`", SYSTEM_PROMPT)
        self.assertIn('"university"', SYSTEM_PROMPT)
        self.assertIn('"student"', SYSTEM_PROMPT)
        self.assertIn('"both"', SYSTEM_PROMPT)

    def test_prompt_defines_markdown_structure_and_answer_types(self) -> None:
        # PART 5: clean Markdown, structure chosen per question type.
        for fragment in (
            "Answer structure (Markdown)",
            "structure/requirements question",
            "comparison question",
            "simple factual question",
            "multi-document question",
            "Markdown table only when a comparison",
        ):
            self.assertIn(fragment, SYSTEM_PROMPT, fragment)

    def test_prompt_defines_comparison_statuses_and_no_over_claiming(self) -> None:
        # PART 9: Present / Missing / Unclear / Not verified + the rule that
        # unseen is not absent (ToC example).
        for fragment in (
            "Comparison accuracy (never over-claim)",
            "**Present**",
            "**Missing**",
            "**Unclear**",
            "**Not verified**",
            'Never mark something Missing just because it was not seen',
            "The table of contents does not show these subsections",
        ):
            self.assertIn(fragment, SYSTEM_PROMPT, fragment)


# ---------------------------------------------------------------------------
# search_documents tool
# ---------------------------------------------------------------------------


class SearchToolTests(SimpleTestCase):
    """The tool exposes RAGService.retrieve() with server-side filters."""

    def setUp(self) -> None:
        self.rag = mock.Mock()
        patcher = mock.patch.object(tools_module, "_rag", self.rag)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_schema_hides_the_injected_session_id(self) -> None:
        self.assertEqual(
            sorted(search_documents.tool_call_schema
                   .model_json_schema()["properties"]),
            ["query", "source"],
        )
        scoped = make_search_documents(str(uuid.uuid4()))
        self.assertEqual(
            sorted(scoped.tool_call_schema.model_json_schema()["properties"]),
            ["query", "source"],
        )
        self.assertEqual(search_documents.name, "search_documents")

    def test_source_filter_is_pushed_down_server_side(self) -> None:
        self.rag.retrieve.return_value = []
        search_documents.invoke({"query": "formatting rules",
                                 "source": "university"})
        self.rag.retrieve.assert_called_once_with(
            query="formatting rules",
            filters={"document_type": "university"},
            top_k=tools_module.RAG_TOP_K,
        )
        self.assertEqual(tools_module.RAG_TOP_K, 5)

    def test_both_source_sends_no_document_type_filter(self) -> None:
        self.rag.retrieve.return_value = []
        search_documents.invoke({"query": "everything", "source": "both"})
        kwargs = self.rag.retrieve.call_args.kwargs
        self.assertNotIn("document_type", kwargs["filters"] or {})
        self.assertIsNone(kwargs["filters"])

    def test_session_scope_is_pushed_down_server_side(self) -> None:
        self.rag.retrieve.return_value = []
        session_id = str(uuid.uuid4())
        scoped = make_search_documents(session_id)
        scoped.invoke({"query": "my thesis", "source": "student"})
        kwargs = self.rag.retrieve.call_args.kwargs
        self.assertEqual(kwargs["filters"],
                         {"document_type": "student", "session_id": session_id})

    def test_invoke_can_override_the_session_id(self) -> None:
        # The LLM cannot send session_id (it is hidden), but direct callers
        # can still scope a call explicitly.
        self.rag.retrieve.return_value = []
        scoped = make_search_documents("session-A")
        scoped.invoke({"query": "q", "session_id": "session-B"})
        kwargs = self.rag.retrieve.call_args.kwargs
        self.assertEqual(kwargs["filters"]["session_id"], "session-B")

    def test_result_carries_citation_blocks_and_the_chunks(self) -> None:
        chunk = make_chunk(page=12, score=0.9123)
        self.rag.retrieve.return_value = [chunk]
        tool = make_search_documents(str(uuid.uuid4()))
        message = tool.run({"query": "methodology", "source": "student"},
                           tool_call_id="call-1")

        self.assertIsInstance(message, ToolMessage)
        self.assertEqual(message.artifact, [chunk])
        for expected in (f"document_id: {chunk.document_id}",
                         "type: student", "page: 12",
                         "section: 2. Methodology", "source_file: thesis.pdf",
                         "score: 0.912"):
            self.assertIn(expected, message.content)

    def test_omitted_page_and_section_are_not_invented(self) -> None:
        chunk = make_chunk(page=None, section="")
        self.rag.retrieve.return_value = [chunk]
        message = make_search_documents().run(
            {"query": "q", "source": "both"}, tool_call_id="call-2")
        self.assertNotIn("page:", message.content)
        self.assertNotIn("section:", message.content)

    def test_empty_results_tell_the_model_not_to_guess(self) -> None:
        self.rag.retrieve.return_value = []
        message = make_search_documents().run(
            {"query": "quantum banana", "source": "student"},
            tool_call_id="call-3")
        self.assertEqual(message.artifact, [])
        self.assertIn("No relevant documents found", message.content)
        self.assertIn("do not guess", message.content)

    def test_empty_results_state_the_evidence_is_insufficient(self) -> None:
        # PART 2.1: no hits -> the agent is told the evidence is
        # insufficient instead of being allowed to hallucinate.
        self.rag.retrieve.return_value = []
        message = make_search_documents().run(
            {"query": "quantum banana", "source": "both"},
            tool_call_id="call-4")
        self.assertIn("insufficient evidence", message.content)

    def test_citation_block_includes_the_file_format(self) -> None:
        chunk = make_chunk(metadata={"source_file": "chapters/intro.tex",
                                     "file_type": "tex"})
        self.rag.retrieve.return_value = [chunk]
        message = make_search_documents().run(
            {"query": "q", "source": "university"}, tool_call_id="call-5")
        self.assertIn("file_type: tex", message.content)

    def test_retrieve_never_receives_the_question_as_a_filter(self) -> None:
        # The query goes as the query argument only: questions are never
        # indexed and never used as metadata filters.
        self.rag.retrieve.return_value = []
        search_documents.invoke({"query": "what is the page limit?",
                                 "source": "university"})
        kwargs = self.rag.retrieve.call_args.kwargs
        self.assertEqual(kwargs["query"], "what is the page limit?")
        self.assertEqual(kwargs["filters"], {"document_type": "university"})


# ---------------------------------------------------------------------------
# ask_nexus
# ---------------------------------------------------------------------------


class _FakeAgent:
    """Stands in for the compiled LangGraph agent (no LLM in tests)."""

    def __init__(self, follow_up: list | None = None,
                 error: Exception | None = None) -> None:
        self.follow_up = follow_up or []
        self.error = error
        self.payload: dict | None = None

    def invoke(self, payload: dict) -> dict:
        self.payload = payload
        if self.error is not None:
            raise self.error
        return {"messages": list(payload["messages"]) + list(self.follow_up)}


class AskNexusTests(TestCase):
    """History handling, question de-duplication and source collection."""

    def setUp(self) -> None:
        self.session = ChatSession.objects.create(title="Session")

    def _history(self, *pairs: tuple[str, str]) -> None:
        for role, content in pairs:
            ChatMessage.objects.create(
                session=self.session,
                role=role,
                content=content,
            )

    def test_history_is_loaded_and_the_question_is_appended_once(self) -> None:
        self._history((ChatMessage.Role.USER, "hello"),
                      (ChatMessage.Role.ASSISTANT, "hi"))
        fake = _FakeAgent([AIMessage(content="grounded answer")])
        with mock.patch.object(agent_module, "create_nexus_agent",
                               return_value=fake) as builder:
            result = ask_nexus("new question", session_id=str(self.session.id))

        builder.assert_called_once_with(str(self.session.id))
        sent = fake.payload["messages"]
        self.assertEqual(
            [(type(m).__name__, m.content) for m in sent],
            [("HumanMessage", "hello"), ("AIMessage", "hi"),
             ("HumanMessage", "new question")],
        )
        self.assertEqual(result.answer, "grounded answer")

    def test_question_already_saved_by_the_view_is_not_sent_twice(self) -> None:
        # The Chat API persists the user turn before calling us.
        self._history((ChatMessage.Role.USER, "hello"),
                      (ChatMessage.Role.ASSISTANT, "hi"),
                      (ChatMessage.Role.USER, "current question"))
        fake = _FakeAgent([AIMessage(content="answer")])
        with mock.patch.object(agent_module, "create_nexus_agent",
                               return_value=fake):
            ask_nexus("current question", session_id=str(self.session.id))

        sent = fake.payload["messages"]
        questions = [m for m in sent
                     if isinstance(m, HumanMessage) and m.content == "current question"]
        self.assertEqual(len(questions), 1)
        self.assertEqual(len(sent), 3)

    def test_sources_are_deduplicated_by_chunk_id(self) -> None:
        chunk_a = make_chunk(chunk_id="chunk-a")
        chunk_b = make_chunk(chunk_id="chunk-b")
        tool_msg = ToolMessage(
            "evidence", tool_call_id="call-1",
            artifact=[chunk_a, chunk_b, chunk_a],  # duplicate chunk_a
        )
        fake = _FakeAgent([tool_msg, AIMessage(content="answer")])
        with mock.patch.object(agent_module, "create_nexus_agent",
                               return_value=fake):
            result = ask_nexus("q", session_id=str(self.session.id))

        self.assertEqual([c.chunk_id for c in result.sources],
                         ["chunk-a", "chunk-b"])

    def test_no_tool_call_means_no_sources(self) -> None:
        fake = _FakeAgent([AIMessage(content="just chatting")])
        with mock.patch.object(agent_module, "create_nexus_agent",
                               return_value=fake):
            result = ask_nexus("q", session_id=str(self.session.id))
        self.assertEqual(result.sources, [])

    def test_list_content_blocks_are_flattened(self) -> None:
        fake = _FakeAgent([AIMessage(content=[{"text": "part one "},
                                              {"text": "part two"}])])
        with mock.patch.object(agent_module, "create_nexus_agent",
                               return_value=fake):
            result = ask_nexus("q", session_id=str(self.session.id))
        self.assertEqual(result.answer, "part one part two")

    def test_missing_assistant_message_raises(self) -> None:
        # History only, no AI answer produced: never return a fake answer.
        self._history((ChatMessage.Role.USER, "q"))
        fake = _FakeAgent([])
        with mock.patch.object(agent_module, "create_nexus_agent",
                               return_value=fake):
            with self.assertRaises(RuntimeError):
                ask_nexus("q", session_id=str(self.session.id))

    def test_history_is_not_mutated_by_the_call(self) -> None:
        # Retrieval context must never be persisted as chat memory.
        self._history((ChatMessage.Role.USER, "q"),
                      (ChatMessage.Role.ASSISTANT, "a"))
        before = list(
            get_messages_for_agent(self.session.id)
        )
        fake = _FakeAgent([ToolMessage("evidence", tool_call_id="c",
                                       artifact=[make_chunk()]),
                           AIMessage(content="answer")])
        with mock.patch.object(agent_module, "create_nexus_agent",
                               return_value=fake):
            ask_nexus("q", session_id=str(self.session.id))

        self.assertEqual(
            ChatMessage.objects.filter(session=self.session).count(), 2
        )
        after = list(get_messages_for_agent(self.session.id))
        self.assertEqual(len(before), len(after))
        for old, new in zip(before, after):
            self.assertEqual(type(old), type(new))
            self.assertEqual(old.content, new.content)


# ---------------------------------------------------------------------------
# state_memory
# ---------------------------------------------------------------------------


class StateMemoryTests(TestCase):
    """Chat rows map to LangChain messages in chronological order."""

    def test_roles_and_order(self) -> None:
        session = ChatSession.objects.create(title="Ordered")
        ChatMessage.objects.create(session=session,
                                   role=ChatMessage.Role.USER, content="one")
        ChatMessage.objects.create(session=session,
                                   role=ChatMessage.Role.ASSISTANT, content="two")

        messages = get_messages_for_agent(session.id)
        self.assertEqual([type(m).__name__ for m in messages],
                         ["HumanMessage", "AIMessage"])
        self.assertEqual([m.content for m in messages], ["one", "two"])

    def test_unknown_session_returns_empty_history(self) -> None:
        self.assertEqual(get_messages_for_agent(uuid.uuid4()), [])


# ---------------------------------------------------------------------------
# POST /api/chat/
# ---------------------------------------------------------------------------


class ChatEndpointTests(TestCase):
    """The frontend contract plus the additive answer/sources fields."""

    def setUp(self) -> None:
        self.url = reverse("chatbot:chat")
        self.document = Document.objects.create(
            title="Lung cancer thesis",
            file_name="Mémoire LungCancer IA.pdf",
            file_path="documents/thesis.pdf",
            source=Document.Source.STUDENT,
        )
        self.chunk = make_chunk(document_id=str(self.document.id),
                                document_type="student")
        self.agent_result = AgentResult(
            answer="The methodology is described in section 2.",
            sources=[self.chunk],
        )

    def test_success_returns_contract_plus_answer_and_sources(self) -> None:
        with mock.patch.object(views_module, "ensure_llm_configured"), \
             mock.patch.object(views_module, "ask_nexus",
                               return_value=self.agent_result):
            response = self.client.post(
                self.url, {"question": "What is the methodology?",
                           "session_id": None},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 201)
        # Existing contract the frontend consumes
        self.assertIn("session_id", response.data)
        self.assertIn("session_title", response.data)
        self.assertEqual(len(response.data["messages"]), 2)
        self.assertEqual(response.data["messages"][0]["role"], "user")
        self.assertEqual(response.data["messages"][1]["role"], "assistant")
        # Additive, grounded fields
        self.assertEqual(response.data["answer"], self.agent_result.answer)
        self.assertEqual(len(response.data["sources"]), 1)
        source = response.data["sources"][0]
        self.assertEqual(source["document_id"], str(self.document.id))
        self.assertEqual(source["document_type"], "student")
        self.assertEqual(source["document_name"],
                         "Mémoire LungCancer IA.pdf")
        self.assertEqual(source["page"], 3)
        self.assertEqual(source["section"], "2. Methodology")
        self.assertEqual(source["score"], 0.8765)

        session = ChatSession.objects.get(pk=response.data["session_id"])
        self.assertEqual(ChatMessage.objects.filter(session=session).count(), 2)

    def test_both_turns_are_saved_in_a_continuing_session(self) -> None:
        session = ChatSession.objects.create(title="Existing")
        ChatMessage.objects.create(session=session,
                                   role=ChatMessage.Role.USER, content="earlier")
        with mock.patch.object(views_module, "ensure_llm_configured"), \
             mock.patch.object(views_module, "ask_nexus",
                               return_value=self.agent_result) as ask:
            response = self.client.post(
                self.url,
                {"question": "And now?",
                 "session_id": str(session.id)},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["session_id"], str(session.id))
        ask.assert_called_once_with("And now?", session_id=str(session.id))
        self.assertEqual(ChatMessage.objects.filter(session=session).count(), 3)

    def test_unknown_session_returns_404(self) -> None:
        response = self.client.post(
            self.url, {"question": "q", "session_id": str(uuid.uuid4())},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 404)
        self.assertEqual(ChatSession.objects.count(), 0)

    def test_invalid_question_returns_400(self) -> None:
        response = self.client.post(
            self.url, {"question": "   "},
            content_type="application/json",
        )
        self.assertEqual(response.status_code, 400)

    def test_missing_llm_key_returns_503_without_persisting_anything(self) -> None:
        error = LLMConfigError(
            "GEMINI_API_KEY is not set. Add it to backend/.env "
            "(GEMINI_API_KEY=...) before using the chat endpoint."
        )
        with mock.patch.object(views_module, "ensure_llm_configured",
                               side_effect=error), \
             mock.patch.object(views_module, "ask_nexus") as ask:
            response = self.client.post(
                self.url, {"question": "q", "session_id": None},
                content_type="application/json",
            )

        self.assertEqual(response.status_code, 503)
        self.assertIn("GEMINI_API_KEY", response.data["detail"])
        self.assertIn("backend/.env", response.data["detail"])
        # No half-persisted turn, and the model never pretended to answer.
        self.assertEqual(ChatSession.objects.count(), 0)
        self.assertEqual(ChatMessage.objects.count(), 0)
        ask.assert_not_called()

    def test_llm_error_after_persisting_the_question_returns_503(self) -> None:
        error = LLMConfigError("GEMINI_MODEL is not set.")
        with mock.patch.object(views_module, "ensure_llm_configured"), \
             mock.patch.object(views_module, "ask_nexus", side_effect=error):
            response = self.client.post(
                self.url, {"question": "q", "session_id": None},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 503)
        self.assertIn("GEMINI_MODEL", response.data["detail"])
        self.assertEqual(ChatSession.objects.count(), 0)
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_agent_failure_returns_502_and_rolls_back_the_turn(self) -> None:
        with mock.patch.object(views_module, "ensure_llm_configured"), \
             mock.patch.object(views_module, "ask_nexus",
                               side_effect=RuntimeError("network down")):
            response = self.client.post(
                self.url, {"question": "q", "session_id": None},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 502)
        self.assertIn("network down", response.data["detail"])
        # The failed turn leaves no orphan rows behind.
        self.assertEqual(ChatSession.objects.count(), 0)
        self.assertEqual(ChatMessage.objects.count(), 0)

    def test_failed_turn_in_an_existing_session_keeps_earlier_history(self) -> None:
        session = ChatSession.objects.create(title="Existing")
        ChatMessage.objects.create(session=session,
                                   role=ChatMessage.Role.USER, content="earlier")
        with mock.patch.object(views_module, "ensure_llm_configured"), \
             mock.patch.object(views_module, "ask_nexus",
                               side_effect=RuntimeError("boom")):
            response = self.client.post(
                self.url, {"question": "new", "session_id": str(session.id)},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 502)
        messages = list(ChatMessage.objects.filter(session=session))
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].content, "earlier")

    def test_empty_research_returns_201_with_no_fabricated_sources(self) -> None:
        with mock.patch.object(views_module, "ensure_llm_configured"), \
             mock.patch.object(views_module, "ask_nexus",
                               return_value=AgentResult(
                                   answer="The documents do not cover this.",
                                   sources=[],
                               )):
            response = self.client.post(
                self.url, {"question": "q", "session_id": None},
                content_type="application/json",
            )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["sources"], [])

    def test_temporary_reply_helper_is_gone(self) -> None:
        self.assertFalse(hasattr(views_module, "_temporary_reply"))


# ---------------------------------------------------------------------------
# sources payload shaping
# ---------------------------------------------------------------------------


class SourcesPayloadTests(TestCase):
    """Every source field is real data; nothing is invented."""

    def setUp(self) -> None:
        self.document = Document.objects.create(
            title="Template",
            file_name="MémoireTemplate.zip",
            file_path="documents/template.zip",
            source=Document.Source.UNIVERSITY,
        )

    def test_empty_list_stays_empty(self) -> None:
        self.assertEqual(views_module._sources_payload([]), [])

    def test_document_name_comes_from_the_document_row(self) -> None:
        chunk = make_chunk(document_id=str(self.document.id),
                           document_type="university",
                           metadata={"source_file": "some-temp-name.docx"})
        [source] = views_module._sources_payload([chunk])
        self.assertEqual(source["document_name"], "MémoireTemplate.zip")

    def test_zip_member_is_cited_as_archive_and_inner_path(self) -> None:
        chunk = make_chunk(
            document_id=str(self.document.id),
            document_type="university",
            metadata={"source_file": "chapter/section-2.docx",
                      "source_archive": "MémoireTemplate.zip"},
        )
        [source] = views_module._sources_payload([chunk])
        self.assertEqual(source["document_name"],
                         "MémoireTemplate.zip / chapter/section-2.docx")

    def test_missing_document_falls_back_to_indexed_metadata(self) -> None:
        chunk = make_chunk(document_id=str(uuid.uuid4()),
                           metadata={"source_file": "original.pdf"})
        [source] = views_module._sources_payload([chunk])
        self.assertEqual(source["document_name"], "original.pdf")

    def test_unknown_page_and_section_stay_none(self) -> None:
        chunk = make_chunk(page=None, section="",
                           document_id=str(self.document.id))
        [source] = views_module._sources_payload([chunk])
        self.assertIsNone(source["page"])
        self.assertEqual(source["section"], "")
        self.assertIn("document_type", source)
        self.assertIn("score", source)

    def test_long_excerpt_is_truncated(self) -> None:
        chunk = make_chunk(text="x" * 900,
                           document_id=str(self.document.id))
        [source] = views_module._sources_payload([chunk])
        self.assertLessEqual(len(source["excerpt"]), 400)
        self.assertTrue(source["excerpt"].endswith("…"))

    def test_score_is_rounded_not_rewritten(self) -> None:
        chunk = make_chunk(score=0.87654321,
                           document_id=str(self.document.id))
        [source] = views_module._sources_payload([chunk])
        self.assertEqual(source["score"], 0.8765)
