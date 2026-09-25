# API

Base URL (development): `http://localhost:8000/api`

Routes are defined in `backend/chatbot/api/urls.py` and mounted under `/api/`
by `backend/config/urls.py`.

## Endpoints

### `GET /api/health/`

Connection check between frontend and backend.

```json
{
  "status": "ok",
  "service": "nexus-backend"
}
```

## Planned endpoints

Not implemented yet — listed here as a sketch, not as a contract:

- `POST /api/documents/` — upload a document
- `GET /api/documents/` — list documents
- `POST /api/chat/` — send a question, receive an answer with sources

Document, chat and agent endpoints will be added together with their services.
