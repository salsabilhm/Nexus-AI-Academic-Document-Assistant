# Service layer of the chatbot application.
# Each module owns one responsibility: document processing
# (document_processor), upload orchestration (document_service), Supabase
# Storage (storage) and workflow orchestration (agent). Retrieval (RAG)
# lives in the sibling chatbot/rag/ package (embedder, vector_store,
# service). See docs/architecture/ for details.
