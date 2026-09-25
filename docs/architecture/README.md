# Architecture

## Layers

```
React Frontend
      ↓
Django REST API
      ↓
Document Processing
      ↓
RAG Retrieval
      ↓
Agent
      ↓
LLM
```

## Responsibilities

| Layer | Owns | Must not do |
|---|---|---|
| **React Frontend** | UI, routing, user interaction, calling the API | hold API keys, talk to the vector DB, contain RAG logic |
| **Django REST API** | endpoints, business logic, database access, authentication | prompt engineering, chunking, embeddings |
| **Document Processing** | extraction, cleaning, chunking, metadata | answering questions, deciding the workflow |
| **RAG Retrieval** | embedding the query, finding relevant passages, returning their sources | generating text, deciding which tool runs |
| **Agent** | choosing the workflow/tool for a request and ordering the steps | low-level retrieval or document parsing details |
| **LLM** | understanding and generating language | storing data, fetching documents |

## Rules of thumb

1. Secrets (LLM keys, DB credentials) live in backend environment variables only.
2. The frontend only ever talks to the Django API.
3. Every assistant answer returns the sources that supported it.
4. Services are independent modules under `chatbot/services/` — each one can be
   replaced without touching the others.

Current state: only the API layer and `GET /api/health/` exist. The service
modules are skeletons with TODOs; no RAG, agent, vector store or LLM is wired.
