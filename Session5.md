# Create only `services/agent/prompts.py` for the Nexus AI Academic Document Assistant.

Define a `SYSTEM_PROMPT` for the Nexus Agent that explains:
- its role as an academic document assistant,
- when to use the document search tool,
- that retrieved documents are the source of truth,
- never to invent information or citations,
- how to handle university requirements, student documents, and comparisons.

Keep the file simple and clean.
Do not modify or create any other files.

---

**Status:** active  **Date:** 2026-09-26

---

### 👤 User

Create only `services/agent/prompts.py` for the Nexus AI Academic Document Assistant.

Define a `SYSTEM_PROMPT` for the Nexus Agent that explains:
- its role as an academic document assistant,
- when to use the document search tool,
- that retrieved documents are the source of truth,
- never to invent information or citations,
- how to handle university requirements, student documents, and comparisons.

Keep the file simple and clean.
Do not modify or create any other files.

---

### 🤖 Assistant

> 🔧 called: list_files



> 🔧 **list_files** — backend/chatbot/services/agent

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — backend/chatbot/services/agent/prompts.py

### 🤖 Assistant

> 🔧 called: read_file, read_file



> 🔧 **read_file** — backend/chatbot/services/agent/agent.py

> 🔧 **read_file** — backend/chatbot/services/agent/tools.py

### 🤖 Assistant

> 🔧 called: read_file



> 🔧 **read_file** — backend/chatbot/services/agent/llm.py

### 🤖 Assistant

> 🔧 called: write_file



> 🔧 **write_file** — backend/chatbot/services/agent/prompts.py

### 🤖 Assistant

[`backend/chatbot/services/agent/prompts.py`](backend/chatbot/services/agent/prompts.py) is written. Here's what it contains:

**`SYSTEM_PROMPT`** is a single module-level string covering six sections:

| Section | What it enforces |
|---|---|
| **Role** | Nexus is strictly an academic document assistant |
| **Using the document search tool** | Always call the tool first; base answers only on what it returns; never fill gaps by guessing |
| **Retrieved documents are the source of truth** | Quote faithfully, always cite the source document |
| **Never invent information or citations** | No fabricated facts, stats, authors, dates, or references |
| **University requirements and guidelines** | Search guideline documents first; present rules in structured lists |
| **Student documents** | Treat with care; stay objective; critique only when explicitly asked |
| **Comparing documents** | Retrieve from each doc and compare structurally; never infer beyond the text |

Import it anywhere in the agent package with:

```python
from .prompts import SYSTEM_PROMPT
```