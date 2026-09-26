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

---

### 👤 User

Create only `backend/chatbot/services/agent/agent.py` for the Nexus AI Academic Document Assistant.

Requirements:
- Use `get_llm()` from `llm.py` to get the Gemini LLM.
- Use `search_documents` from `tools.py` as the Agent tool.
- Use `SYSTEM_PROMPT` from `prompts.py`.
- Create the Nexus Agent with the current LangChain API using `create_agent`.
- Implement `create_nexus_agent()` to create and configure the agent.
- Implement `ask_nexus(question: str)` to invoke the agent with the user's question and return the result.
- The Agent must rely on the LLM for understanding the user's question and deciding when to use `search_documents`.
- Do not implement document preprocessing, RAG, embeddings, pgvector, or tool logic in this file.
- Do not create or modify any other files.
- Keep the code simple, clean, typed, and compatible with the project's installed LangChain version.

---

### 🤖 Assistant

> 🔧 called: execute_command, read_file

Let me check the installed LangChain version and the existing agent patterns before writing anything.

> 🔧 **execute_command** — pip show langchain-core langchain langchain-google-genai 2>&1

> 🔧 **read_file** — backend/requirements.txt

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — pip show langchain-core langchain langchain-google-genai --no-color 2>&1; py -m pip show langchain-core langchain langchain-google-genai 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — Get-ChildItem Env: | Where-Object { $_.Name -like "*VIRTUAL*" -or $_.Name -like "*CONDA*" -or $_.Name -like "*PYTHON*" } | Select-Object Name, Value

### 🤖 Assistant

> 🔧 called: glob, glob



> 🔧 **glob** — backend/**/activate*

> 🔧 **glob** — **/*venv*/**/*.cfg

### 🤖 Assistant

> 🔧 called: glob, glob



> 🔧 **glob** — **/*pyvenv*

> 🔧 **glob** — **/*.cfg

### 🤖 Assistant

> 🔧 called: execute_command, execute_command



> 🔧 **execute_command** — Get-Command python, python3 -ErrorAction SilentlyContinue | Select-Object Name, Source

> 🔧 **execute_command** — Get-ChildItem . -Filter "*.txt" -Recurse | Where-Object { $_.Name -like "*require*" } | Select-Object FullName

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — & "C:\Users\INFO PC\AppData\Local\Programs\Python\Python311\python.exe" -m pip show langchain-core langchain langchain-google-genai 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — & "C:\Users\INFO PC\AppData\Local\Programs\Python\Python311\python.exe" -m pip list 2>&1 | Select-String "langchain"

### 🤖 Assistant

> 🔧 called: execute_command

The packages are not installed in the global Python. Let me find the project's virtual environment.

> 🔧 **execute_command** — Get-ChildItem . -Recurse -Filter "python.exe" -ErrorAction SilentlyContinue | Select-Object FullName | Select-Object -First 5

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -m pip show langchain-core langchain langchain-google-genai 2>&1

### 🤖 Assistant

> 🔧 called: execute_command, execute_command

LangChain 1.4.2 and LangChain-core 1.6.5 are installed — these are the very latest major versions. Let me check what agent APIs are available:

> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "import langchain; print(dir(langchain))"

> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -m pip show langgraph langgraph-prebuilt 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "from langgraph.prebuilt import create_react_agent; help(create_react_agent)" 2>&1 | Select-Object -First 40

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "from langchain.agents import create_agent; help(create_agent)" 2>&1 | Select-Object -First 80

### 🤖 Assistant

> 🔧 called: execute_command, execute_command

Now I have everything I need. The installed stack is `langchain==1.4.2` / `langchain-core==1.6.5` / `langgraph==1.2.12`, and the current API is `langchain.agents.create_agent` (not `create_react_agent`). Let me also confirm the invoke signature:

> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "
from langchain.agents import create_agent
import inspect
sig = inspect.signature(create_agent)
print(sig)
" 2>&1

> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "
from langchain.agents.factory import create_agent
# check what invoke returns / how to call it
import langchain
print('langchain version:', langchain.__version__)
from langchain_core.messages import HumanMessage
print(HumanMessage.__module__)
" 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "
from langchain.agents.factory import create_agent
# Check the InputAgentState / invoke input shape
from langchain.agents.schema import InputAgentState, OutputAgentState, AgentState
print('InputAgentState fields:', InputAgentState.__annotations__ if hasattr(InputAgentState, '__annotations__') else dir(InputAgentState))
" 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "
import langchain.agents as la
print(dir(la))
" 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "
from langchain.agents import AgentState
print(AgentState.__annotations__)
import typing, inspect
print(inspect.getmro(AgentState))
" 2>&1

### 🤖 Assistant

> 🔧 called: execute_command



> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "
from langchain.agents import create_agent, AgentState
from langchain_core.messages import HumanMessage

# Check how invoke works on a compiled graph
import inspect
from langgraph.graph.state import CompiledStateGraph
invoke_sig = inspect.signature(CompiledStateGraph.invoke)
print('invoke signature:', invoke_sig)
" 2>&1

### 🤖 Assistant

> 🔧 called: write_file

Now I have the complete picture. The correct pattern is:
- `create_agent(model, tools, system_prompt=...)` → returns a `CompiledStateGraph`
- Invoke it with `{"messages": [HumanMessage(content=question)]}` 
- The result is a dict with a `"messages"` list; the last message is the final AI response

> 🔧 **write_file** — backend/chatbot/services/agent/agent.py

### 🤖 Assistant

> 🔧 called: execute_command

Now let me verify the imports resolve cleanly against the installed packages:

> 🔧 **execute_command** — & ".\.venv\Scripts\python.exe" -c "
from langchain.agents import create_agent
from langchain_core.messages import HumanMessage
from langgraph.graph.state import CompiledStateGraph
print('All imports OK')
" 2>&1

### 🤖 Assistant

All imports resolve. [`agent.py`](backend/chatbot/services/agent/agent.py) is done. Here's what was built and why each decision was made:

---

### What was built

Two public functions, nothing else:

#### [`create_nexus_agent()`](backend/chatbot/services/agent/agent.py:27)
Calls `langchain.agents.create_agent` — the **current** API in `langchain==1.4.2` (not the deprecated `create_react_agent` from `langgraph.prebuilt`, which the help text itself flags as deprecated). It passes:
- `model=get_llm()` — Gemini instance from [`llm.py`](backend/chatbot/services/agent/llm.py)
- `tools=[search_documents]` — the single tool from [`tools.py`](backend/chatbot/services/agent/tools.py)
- `system_prompt=SYSTEM_PROMPT` — the string from [`prompts.py`](backend/chatbot/services/agent/prompts.py)

Returns a `CompiledStateGraph` — the real return type of `create_agent`, verified against the live signature.

#### [`ask_nexus(question: str) -> str`](backend/chatbot/services/agent/agent.py:50)
Wraps the graph in the simplest possible call path:

| Step | What & why |
|---|---|
| `agent.invoke({"messages": [HumanMessage(...)]})` | `AgentState` has a single required key `messages: list[AnyMessage]` — confirmed by introspecting `AgentState.__annotations__` in the installed package. |
| `result["messages"][-1].content` | The graph appends every message (tool calls, tool results, final AI reply) to the list. The last entry is always the final `AIMessage`. |
| `str(...)` | `content` can be `str` or `list` (multi-part Gemini responses); `str()` keeps the return type clean and typed. |
| Fresh agent per call | Stateless by design; no checkpointer is passed, so no cross-call memory leaks — appropriate until a session/thread model is defined. |

---

### 👤 User

I want you to implement a new file called `state_memory.py` inside:

backend/chatbot/services/agent/

Context:
Nexus is an AI Academic Document Assistant built with Django, LangChain, Gemini, and RAG.

The Agent architecture is:

User
→ Django Backend
→ Nexus Agent
→ Gemini + Tools
→ RAG
→ PostgreSQL / pgvector

The Django backend already contains these models:

- ChatSession: represents one conversation session.
- ChatMessage: stores the messages belonging to a ChatSession.
- ChatMessage has a role (USER or ASSISTANT), content, and created_at.

The purpose of `state_memory.py` is ONLY to manage conversation memory between Django's database and the LangChain Agent.

IMPORTANT:
- Do NOT implement an LLM here.
- Do NOT create or configure Gemini here.
- Do NOT implement the Agent here.
- Do NOT implement RAG here.
- Do NOT access pgvector directly.
- Do NOT create a second database or an in-memory global message list.
- Use the existing Django `ChatSession` and `ChatMessage` models.
- Use Django ORM for database access.
- Use LangChain message types for the Agent.
- Do not modify existing models.py.

Create these four functions:

1. `get_conversation_history(session_id)`
   - Retrieve all ChatMessage objects belonging to the given session.
   - Order them chronologically using `created_at`.
   - Return the conversation history.

2. `save_user_message(session_id, content)`
   - Create and save a ChatMessage with role USER.
   - Associate it with the given ChatSession.

3. `save_assistant_message(session_id, content)`
   - Create and save a ChatMessage with role ASSISTANT.
   - Associate it with the given ChatSession.

4. `get_messages_for_agent(session_id)`
   - Retrieve the conversation history using `get_conversation_history()`.
   - Convert USER messages to LangChain `HumanMessage`.
   - Convert ASSISTANT messages to LangChain `AIMessage`.
   - Return a list of LangChain messages ready to be passed to the Agent.

Expected structure:

backend/
└── chatbot/
    └── services/
        └── agent/
            ├── agent.py
            ├── llm.py
            ├── tools.py
            ├── prompts.py
            └── state_memory.py

Expected imports:

from langchain_core.messages import HumanMessage, AIMessage
from ...models import ChatMessage

Use the existing `ChatMessage.Role.USER` and `ChatMessage.Role.ASSISTANT` constants instead of hardcoded role strings if they are available in the model.

Keep the implementation simple and appropriate for an MVP.

Add clear docstrings and type hints where appropriate.

Do not modify any other file.

After creating the file, explain briefly:
1. What each function does.
2. How `state_memory.py` interacts with Django/PostgreSQL.
3. How `get_messages_for_agent()` prepares the conversation history for the LangChain Agent.

---

### 🤖 Assistant

> 🔧 called: glob, list_files

Let me read the existing models before writing a single line.

> 🔧 **list_files** — backend/chatbot

> 🔧 **glob** — backend/chatbot/models.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — backend/chatbot/models.py

### 🤖 Assistant

> 🔧 called: write_file

I have everything I need. Key facts confirmed from the model:
- `ChatMessage.Role.USER = "user"`, `ChatMessage.Role.ASSISTANT = "assistant"` — TextChoices constants exist
- `ChatMessage.session` is a FK to `ChatSession`
- `ChatMessage.created_at` is the ordering field
- The `Meta` on `ChatMessage` already orders by `["session", "created_at"]`
- `session_id` is the UUID PK of `ChatSession`

> 🔧 **write_file** — backend/chatbot/services/agent/state_memory.py

### 🤖 Assistant

> 🔧 called: list_files, read_file

Now verify the relative import path is correct — `state_memory.py` is at `backend/chatbot/services/agent/`, so `...models` should resolve to `backend/chatbot/models`:

> 🔧 **list_files** — backend/chatbot/services

> 🔧 **read_file** — backend/chatbot/services/__init__.py

### 🤖 Assistant

> 🔧 called: glob, read_file



> 🔧 **read_file** — backend/chatbot/__init__.py

> 🔧 **glob** — backend/chatbot/services/agent/__init__.py

### 🤖 Assistant

> 🔧 called: grep, grep

The `agent/` directory has no `__init__.py` — let me check how the other agent files import from `...models` to confirm the depth is consistent:

> 🔧 **grep** — from \.\.

> 🔧 **grep** — from \.\.

### 🤖 Assistant

The depth is correct: `tools.py` uses `..rag` (one level up = `services/`), and `state_memory.py` uses `...models` (three levels up = `chatbot/`). Let me trace the path explicitly:

```
agent/state_memory.py  →  ...  →  chatbot/models.py
  .   = agent/
  ..  = services/
  ... = chatbot/          ✓
```

The import is correct. The file is complete.

---

### What each function does

#### 1. [`get_conversation_history(session_id)`](backend/chatbot/services/agent/state_memory.py:27)
Issues a single `SELECT … WHERE session_id = ? ORDER BY created_at ASC` via the Django ORM. Returns a plain Python `list` of `ChatMessage` rows — oldest message first. This is the only place that touches the database for reads; the other functions call it rather than querying independently.

#### 2. [`save_user_message(session_id, content)`](backend/chatbot/services/agent/state_memory.py:50)
Issues a single `INSERT INTO chat_messages` with `role = ChatMessage.Role.USER` (`"user"`). Returns the newly created row. Uses the model constant — not a hardcoded string — so a future rename in the model propagates automatically.

#### 3. [`save_assistant_message(session_id, content)`](backend/chatbot/services/agent/state_memory.py:68)
Identical to the above but with `role = ChatMessage.Role.ASSISTANT` (`"assistant"`). Called after the agent replies, before the response is sent to the client.

#### 4. [`get_messages_for_agent(session_id)`](backend/chatbot/services/agent/state_memory.py:87)
Calls `get_conversation_history()` then maps each row to its LangChain counterpart:

| DB `role` value | LangChain type |
|---|---|
| `ChatMessage.Role.USER` | `HumanMessage(content=…)` |
| `ChatMessage.Role.ASSISTANT` | `AIMessage(content=…)` |

Returns a `list[BaseMessage]` that can be dropped straight into the agent's input dict as `{"messages": get_messages_for_agent(session_id)}`.

---

### How `state_memory.py` interacts with Django / PostgreSQL

It is a pure Django ORM layer. Every read/write goes through `ChatMessage.objects` — Django handles connection pooling, parameterised queries, and transactions. No raw SQL, no second connection, no in-memory cache. The `session_id` foreign key keeps every message scoped to exactly one `ChatSession` row in the `chat_sessions` table.

---

### How `get_messages_for_agent()` prepares history for the agent

The LangChain agent built in [`agent.py`](backend/chatbot/services/agent/agent.py) expects its input as:

```python
{"messages": [HumanMessage(...), AIMessage(...), HumanMessage(...), ...]}
```

`get_messages_for_agent()` produces exactly that list. Because the messages are ordered by `created_at` (oldest first), the agent receives the full, chronologically-correct conversation context, allowing it to understand follow-up questions, resolve pronouns, and avoid repeating information it already provided.