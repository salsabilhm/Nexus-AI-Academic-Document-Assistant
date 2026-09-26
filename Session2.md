# Please first read and understand the existing `README.md` and the current project structure of Nexus.

I am responsible for implementing the **AI Agent layer** of the project.

Before writing any code:

1. Analyze the existing README and project structure.
2. Identify the role of the AI Agent in the overall Nexus architecture.
3. Clearly distinguish the Agent layer from the RAG layer.
4. Identify which components/tools the Agent needs to interact with.
5. Propose a clean Agent architecture using **LangChain + Gemini**.
6. Do not implement the complete RAG pipeline because another team member is responsible for it.

For now, only provide the architecture, required files, responsibilities of each component, and the interaction flow.

Do not modify the project yet.

---

**Status:** active  **Date:** 2026-09-25

---

### 👤 User

Please first read and understand the existing `README.md` and the current project structure of Nexus.

I am responsible for implementing the **AI Agent layer** of the project.

Before writing any code:

1. Analyze the existing README and project structure.
2. Identify the role of the AI Agent in the overall Nexus architecture.
3. Clearly distinguish the Agent layer from the RAG layer.
4. Identify which components/tools the Agent needs to interact with.
5. Propose a clean Agent architecture using **LangChain + Gemini**.
6. Do not implement the complete RAG pipeline because another team member is responsible for it.

For now, only provide the architecture, required files, responsibilities of each component, and the interaction flow.

Do not modify the project yet.

---

### 🤖 Assistant

> 🔧 called: read_file, list_files



> 🔧 **read_file** — README.md

> 🔧 **list_files** — .

### 🤖 Assistant

> 🔧 called: list_files, list_files



> 🔧 **list_files** — docs

> 🔧 **list_files** — backend

### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file



> 🔧 **read_file** — backend/chatbot/services/document_processor.py

> 🔧 **read_file** — backend/chatbot/services/agent.py

> 🔧 **read_file** — backend/chatbot/services/rag.py

### 🤖 Assistant

> 🔧 called: read_file, read_file, read_file, read_file



> 🔧 **read_file** — backend/chatbot/models.py

> 🔧 **read_file** — backend/chatbot/api/views.py

> 🔧 **read_file** — backend/chatbot/api/urls.py

> 🔧 **read_file** — docs/architecture/README.md

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — backend/chatbot/api/serializers.py

> 🔧 **read_file** — backend/requirements.txt

### 🤖 Assistant

> 🔧 called: create_html_artifact

Now I have a thorough understanding of the entire project. Let me compose the architecture proposal.

> 🔧 **create_html_artifact** — nexus_agent_architecture

### 🤖 Assistant

Here is the full architecture proposal — no files have been touched.

---

## Summary of findings

### Where the Agent sits

The README and `docs/architecture/README.md` both place the Agent as the **layer between RAG and the LLM**. It is the decision-maker and orchestrator; it never does retrieval or document parsing.

---

### Agent vs RAG — the hard boundary

| Concern | RAG (teammate) | Agent (you) |
|---|---|---|
| Embedding, vector store, `retrieve()` | ✔ owns | ✘ only calls |
| Deciding whether/what to retrieve | ✘ | ✔ owns |
| Calling the LLM, prompt construction | ✘ | ✔ exclusively |
| Assembling answer + citations | ✘ | ✔ exclusively |

The contract is already defined: [`RagService.retrieve(query, top_k) -> list[RetrievedPassage]`](backend/chatbot/services/rag.py:36). You consume it; you do not implement it.

---

### Proposed file structure

The single [`agent.py`](backend/chatbot/services/agent.py) skeleton becomes a small package under `chatbot/services/agent/`:

| File | Responsibility |
|---|---|
| `llm.py` | Builds `ChatGoogleGenerativeAI` from env vars — credentials only here |
| `state.py` | `AgentState(TypedDict)` — the shared state passed between graph nodes |
| `prompts.py` | All `ChatPromptTemplate` objects — `INTENT_PROMPT`, `QA_PROMPT`, `COMPARE_PROMPT` |
| `tools.py` | Wraps `RagService.retrieve` as a LangChain `Tool` |
| `nodes.py` | Pure node functions: `classify_intent`, `retrieve_context`, `generate_answer`, `compare_documents`, `build_citations` |
| `graph.py` | LangGraph `StateGraph` — wires nodes together with conditional edges |
| `agent.py` | Public `Agent` class: compiles the graph, exposes `run(question) -> AgentResult` |

---

### Key design decisions

1. **LangGraph** is used instead of a raw chain because the QA path and the comparison path are distinct workflows — a graph with conditional edges expresses this cleanly.
2. **Nodes are pure functions** — no Django ORM, no side effects. The view layer handles persistence.
3. **`Agent(rag_service=...)` is injected**, not hardcoded — this makes unit testing straightforward with a mock.
4. The public signature `Agent.run(question) -> AgentResult` is **backward-compatible** with the existing skeleton, so the views team is not blocked.
5. All four required packages (`langchain`, `langchain-google-genai`, `langgraph`, `langchain-core`) are **already installed** in `.venv` — only `requirements.txt` needs updating when implementation begins.

---

### 👤 User

give me a structure of ai agent

---

### 🤖 Assistant

> 🔧 called: list_files



> 🔧 **list_files** — backend/chatbot/services

### 🤖 Assistant

Based on the architecture we just designed, here is the exact folder/file structure the Agent layer will have:

```
backend/
└── chatbot/
    └── services/
        ├── rag.py                        ← teammate's (you only import from it)
        ├── document_processor.py         ← teammate's (you never touch it)
        │
        └── agent/                        ← YOUR package (replaces agent.py skeleton)
            ├── __init__.py               ← re-exports Agent + AgentResult
            │
            ├── llm.py                    ← Gemini LLM factory (credentials only here)
            ├── state.py                  ← AgentState TypedDict (shared graph state)
            ├── prompts.py                ← all ChatPromptTemplates
            ├── tools.py                  ← LangChain Tool wrapper over RagService
            ├── nodes.py                  ← graph node functions (pure, no side effects)
            ├── graph.py                  ← LangGraph StateGraph (wires nodes + routing)
            └── agent.py                  ← public Agent class → run() → AgentResult
```

---

### What each file does in one line

| File | One-line job |
|---|---|
| [`__init__.py`](backend/chatbot/services/agent/__init__.py) | `from .agent import Agent, AgentResult` — nothing else |
| [`llm.py`](backend/chatbot/services/agent/llm.py) | `get_llm()` reads `GEMINI_API_KEY` from env, returns one `ChatGoogleGenerativeAI` singleton |
| [`state.py`](backend/chatbot/services/agent/state.py) | Declares `AgentState(TypedDict)` with fields: `question`, `intent`, `passages`, `answer`, `citations` |
| [`prompts.py`](backend/chatbot/services/agent/prompts.py) | Three `ChatPromptTemplate` objects: `INTENT_PROMPT`, `QA_PROMPT`, `COMPARE_PROMPT` |
| [`tools.py`](backend/chatbot/services/agent/tools.py) | Wraps `RagService.retrieve()` as a `Tool` so the graph calls it uniformly |
| [`nodes.py`](backend/chatbot/services/agent/nodes.py) | Five node functions: `classify_intent → retrieve_context → generate_answer / compare_documents → build_citations` |
| [`graph.py`](backend/chatbot/services/agent/graph.py) | Builds the `StateGraph`, adds nodes, adds conditional edges, compiles it |
| [`agent.py`](backend/chatbot/services/agent/agent.py) | `Agent.run(question) → AgentResult` — the only class the Django view imports |

---

### Data flow through the files

```
Django view
    │
    ▼
agent.py  ──── compiles ────▶  graph.py
                                   │
                         ┌─────────┴──────────┐
                         ▼                    ▼
                     state.py            nodes.py
                  (AgentState)       ┌───────────────┐
                                     │ classify_intent│◀── prompts.py (INTENT_PROMPT)
                                     │       ↓        │        + llm.py
                                     │retrieve_context│◀── tools.py → rag.py
                                     │       ↓        │
                                     │generate_answer │◀── prompts.py (QA_PROMPT)
                                     │  OR compare    │        + llm.py
                                     │       ↓        │
                                     │build_citations │ (pure Python)
                                     └───────────────┘
                         │
                         ▼
                    AgentResult
                 (answer + passages)
                         │
                         ▼
                    Django view → JSON response
```

This is the complete structure. Ready to implement when you say go.