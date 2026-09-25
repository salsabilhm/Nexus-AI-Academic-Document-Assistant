# Database

## Current state

No application tables exist yet. `chatbot/models.py` is intentionally empty —
models are added when the first endpoint actually needs them.

## Engine

- **Production:** PostgreSQL, configured through `DATABASE_URL`
  (see `backend/.env.example`).
- **Local development:** falls back to SQLite (`backend/db.sqlite3`, ignored by
  Git) when `DATABASE_URL` is unset or uses the `sqlite` scheme.

## Likely future models

- `Document` — name, type, status, storage path, upload timestamp
- `Conversation` / `Message` — chat history per user
- `SourceLink` — which document passage supported a given answer

Chosen indexes/vector storage for retrieval will be documented here once the
RAG layer is designed. Nothing is decided today.
