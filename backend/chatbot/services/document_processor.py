"""Document processing service.

Responsibility: turn uploaded files into clean, retrievable text.

Future pipeline (not implemented yet):
    extract text -> clean/normalize -> split into chunks -> attach metadata

TODO:
- accept PDF/DOCX/TXT/MD files and extract their text;
- normalize whitespace, headings and page markers;
- chunk documents with stable IDs and source metadata (file, page/section);
- store processed content where the RAG layer can read it.

This module must stay independent from Django views and from the LLM layer.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class ProcessedChunk:
    """A single chunk produced from an uploaded document."""

    chunk_id: str
    document_id: str
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)


class DocumentProcessor:
    """Extracts, cleans and chunks documents. Implementation comes later."""

    def process(self, file_path: Path) -> list[ProcessedChunk]:
        """Return the chunks of a document.

        TODO: implement extraction, cleaning and chunking.
        """
        raise NotImplementedError(
            "DocumentProcessor.process is a skeleton; document processing is not implemented yet."
        )
