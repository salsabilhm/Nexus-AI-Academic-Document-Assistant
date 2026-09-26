
# Nexus — AI Academic Document Assistant

Nexus helps university students work with their academic documents. Upload
university requirements, guidelines and templates alongside your own research,
then ask Nexus what is missing, unclear or out of place — with the sources
behind every answer.

## Problem

Students routinely check a thesis or report against a pile of PDFs: faculty
requirements, formatting guidelines, assessment criteria. It is slow, easy to
miss a section, and hard to know which rule came from which document.

## Planned solution

Nexus reads those documents once and then:

- retrieves the parts relevant to your question;
- compares university requirements with your research document;
- flags missing or unclear sections;
- gives recommendations grounded in the documents, not in guesswork;
- answers questions in a chatbot, showing the source for every answer.

## Architecture

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

Each layer has one job. The frontend never sees API keys or the vector
database; the API never contains prompt logic; retrieval never generates text.
Details in [`docs/architecture/`](docs/architecture/README.md).

## Tech stack

**Frontend:** React, TypeScript, Vite, Tailwind CSS, React Router, Axios
**Backend:** Python, Django, Django REST Framework, django-cors-headers, PostgreSQL (psycopg), python-dotenv

## Project structure

```
nexus/
├── frontend/     React + TypeScript SPA (Vite, Tailwind)
├── backend/      Django REST API (config/ + chatbot/ app)
│   └── chatbot/
│       ├── api/        serializers, views, urls
│       └── services/   document_processor, rag, agent (skeletons)
├── dataset/      university and student documents (added later)
├── docs/         architecture, api, database notes
└── docker-compose.yml
```

## Local installation

Prerequisites: Node 20+, Python 3.10+, Git.

```bash
git clone <your-repo-url>
cd nexus
```

### Frontend

```bash
cd frontend
npm install
cp .env.example .env
npm run dev            # http://localhost:5173
```

### Backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate      # macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # adjust values as needed
python manage.py migrate
python manage.py runserver  # http://localhost:8000
```

Check the connection: `GET http://localhost:8000/api/health/` →

```json
{ "status": "ok", "service": "nexus-backend" }
```

## Environment variables

| File | Variable | Purpose |
|---|---|---|
| `frontend/.env` | `VITE_API_BASE_URL` | API base URL used by Axios |
| `backend/.env` | `SECRET_KEY`, `DEBUG` | Django core settings |
| `backend/.env` | `DATABASE_URL` | PostgreSQL connection string |
| `backend/.env` | `ALLOWED_HOSTS`, `CORS_ALLOWED_ORIGINS` | host/CORS control |
| `backend/.env` | `LLM_API_KEY` (empty) | placeholder for a future LLM |

Copy each `.env.example` to `.env`. `.env` files are ignored by Git — never
commit real keys.

## Running with Docker

```bash
docker compose up --build
```

- frontend → http://localhost:5173
- backend → http://localhost:8000/api/health/
- PostgreSQL → localhost:5432

## Git workflow

```bash
git checkout -b feat/your-feature
# …make changes…
git add .
git commit -m "feat: describe your change"
git push -u origin feat/your-feature
```

Commit prefixes: `feat`, `fix`, `chore`, `docs`, `refactor`, `test`.
Keep `.env`, `node_modules/`, `.venv/`, `dist/` and database files out of
commits — the root `.gitignore` already covers them.

## Roadmap

1. **Documents** — upload, extraction, cleaning and chunking.
2. **Retrieval** — embeddings, vector store, relevant-passage search.
3. **Chat** — agent workflow, answers grounded in retrieved context.
4. **Comparison** — check a student document against university requirements.
5. **Feedback** — missing/unclear sections with cited sources.

Current status: project skeleton only. Routing, health endpoint and the
service layer structure are in place; RAG, the agent and LLM integration are
intentionally not implemented yet.
=======
# Nexus-AI-Academic-Document-Assistant
Nexus helps university students compare their research documents with university-specific requirements and identify missing or unclear sections, while providing source-grounded recommendations.
