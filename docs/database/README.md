# Database

## Current state

`chatbot/models.py` defines five tables (migrations `0001`–`0003`):

| Table | Purpose |
| --- | --- |
| `documents` | uploaded file metadata (title, source `university`/`student`, status, Supabase Storage key, chat session it was uploaded in) |
| `document_chunks` | text chunks extracted by `DocumentProcessor` (the durable source of truth for chunk text) |
| `document_vectors` | **retrieval index**: one row per embedded chunk — pgvector `embedding vector(384)` + filterable metadata columns |
| `chat_sessions` | one conversation per session |
| `chat_messages` | individual turns inside a session (`user` / `assistant`) |

## Engine

- **Production:** PostgreSQL (Supabase), configured through `DATABASE_URL`
  (see `backend/.env.example`).
- **Local development:** falls back to SQLite (`backend/db.sqlite3`, ignored by
  Git) when `DATABASE_URL` is unset or uses the `sqlite` scheme.
  Note: the RAG vector table uses the **pgvector** extension, which requires
  PostgreSQL — SQLite cannot host `document_vectors`.

## Vector storage (RAG layer)

Decided in the RAG step (see `backend/chatbot/rag/`):

- **Extension:** pgvector (`CREATE EXTENSION vector`, migration
  `0003_documentvector`, operation `VectorExtension()` — idempotent).
- **Column:** `document_vectors.embedding vector(384)` — dimension fixed by
  `chatbot.rag.embedder.DEFAULT_DIMENSION`. Changing the embedding model's
  dimension means a migration **and** a full re-index.
- **Filter columns:** `document_type` (university/student), `session_id`,
  `document_id`, plus `page` / `section` for citations; remaining processor
  metadata lives in the `metadata` JSON column. `document_type` has a b-tree
  index (`dv_document_type_idx`).
- **Similarity:** cosine (`embedding <=> $query`), `score = 1 - distance`.
  No ANN index (HNSW/IVFFlat) yet: at MVP scale a sequential scan over a few
  thousand rows is optimal; add `HnswIndex` when the corpus grows.
- **Access:** raw SQL through `chatbot/rag/vector_store.py` (values passed
  with explicit `::vector` / `::jsonb` casts; the embedding column is never
  read back), so no client-side pgvector type registration is required.

## Future models

- `SourceLink` — which document passage supported a given answer (once the
  Agent/LLM layer reports citations).
