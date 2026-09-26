"""Retrieval (RAG) package — the two functions of the pipeline: index() and retrieve().

Layout (see docs/architecture/):
    rag/
    ├── service.py       — RAGService.index(chunks) / RAGService.retrieve(query, filters, top_k)
    ├── embedder.py      — Text -> Embedding (pure Python, no Django, no Agent)
    └── vector_store.py  — Embedding + Metadata -> pgvector / Query + Filters -> Similar Chunks

Import the classes from their modules, e.g.::

    from chatbot.rag.service import RAGService

This package's ``__init__`` intentionally exports nothing: chatbot.models
imports ``chatbot.rag.embedder.DEFAULT_DIMENSION`` for the vector column
size, so re-exporting modules that import the models would create a
circular import.
"""
