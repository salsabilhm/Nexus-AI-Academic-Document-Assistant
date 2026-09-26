# Create only `services/agent/tools.py` for the Nexus AI Academic Document Assistant.

Implement one LangChain tool: `search_documents(query, source="both")`.

Requirements:
- `source` must support: `university`, `student`, `both`.
- The tool must search documents through the existing RAG service.
- Do not implement PDF/TEX/JAVA preprocessing, embeddings, pgvector, or agent logic here.
- Keep the code simple, clean, and typed.
- Reuse the existing RAG interface; do not invent a new one.
- Do not modify or create any other files.

---

**Status:** active  **Date:** 2026-09-26

---

### 👤 User

Create only `services/agent/tools.py` for the Nexus AI Academic Document Assistant.

Implement one LangChain tool: `search_documents(query, source="both")`.

Requirements:
- `source` must support: `university`, `student`, `both`.
- The tool must search documents through the existing RAG service.
- Do not implement PDF/TEX/JAVA preprocessing, embeddings, pgvector, or agent logic here.
- Keep the code simple, clean, and typed.
- Reuse the existing RAG interface; do not invent a new one.
- Do not modify or create any other files.

---

### 🤖 Assistant

> 🔧 called: list_files, glob

Let me first explore the existing codebase to understand the RAG interface before writing anything.

> 🔧 **list_files** — backend/chatbot/services

> 🔧 **glob** — backend/**/*.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — backend/chatbot/services/agent/tools.py

> 🔧 **read_file** — backend/chatbot/services/rag.py

### 🤖 Assistant

> 🔧 called: read_file, read_file

Now let me also check the agent files for any existing patterns or imports to follow:

> 🔧 **read_file** — backend/chatbot/services/agent/agent.py

> 🔧 **read_file** — backend/chatbot/services/agent/llm.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — backend/chatbot/services/agent/prompts.py

> 🔧 **read_file** — backend/requirements.txt

### 🤖 Assistant

> 🔧 called: write_file

Now I have a complete picture of the codebase. Here's what I know:

- [`RagService`](backend/chatbot/services/rag.py:33) exposes a single `retrieve(query, top_k)` method returning `list[RetrievedPassage]`
- `RetrievedPassage` has `text`, `document_id`, `document_name`, `metadata`, `score`
- The project uses `langchain-google-genai` — LangChain is already a dependency
- The `source` filter (`university` / `student` / `both`) maps naturally onto `RetrievedPassage.metadata`
- The tool must be a LangChain tool (decorated function), not a new RAG implementation

> 🔧 **write_file** — backend/chatbot/services/agent/tools.py

### 🤖 Assistant

[`tools.py`](backend/chatbot/services/agent/tools.py) is done. Here's a walkthrough of every decision:

---

### What was built

**`search_documents`** — a single `@tool`-decorated function that the LangChain agent can call by name.

| Concern | Decision |
|---|---|
| **RAG interface** | Calls `_rag.retrieve(query)` — exactly the method [`RagService`](backend/chatbot/services/rag.py:36) declares. Nothing invented. |
| **Source filtering** | `source` is typed as `Literal["university", "student", "both"]`. Filtering is a post-retrieve list comprehension on `passage.metadata["source"]`, which is the natural home for that field in [`RetrievedPassage`](backend/chatbot/services/rag.py:23). |
| **No results path** | Returns a clear human-readable string (not an exception) so the agent can relay it to the user gracefully. |
| **Formatting** | `_format_passage` renders `document_name`, `text`, and `score` — all fields already on `RetrievedPassage` — separated by `---` dividers so the agent sees distinct blocks. |
| **Shared instance** | `_rag` is module-level. `RagService` has no state today; when it does, it can be injected via a factory without changing the tool's signature. |
| **LangChain import** | Uses `langchain_core.tools.tool` — `langchain-google-genai` already pulls in `langchain-core` as a dependency (no new requirement). |