"""Document processing service.

Responsibility: turn uploaded files into clean, retrievable, chunked
content ready for embeddings and RAG.

Supported file types
---------------------
    .pdf   .docx   .txt   .md            (text, page/section aware)
    .tex                                  (LaTeX, chapter/section aware)
    .cls                                  (LaTeX class -> formatting rules)
    .bib                                  (BibTeX -> structured citations)
    .java                                 (class/method aware)
    .png .jpg .jpeg                       (metadata + pluggable OCR/Vision)
    .zip                                  (container: securely unpacked,
                                            each member routed to the
                                            extractor above matching its
                                            own extension)

Pipeline
--------
    File
     |
     v
    Extraction         (per-type extractor; .zip is fanned out first)
     |
     v
    Cleaning           (TextCleaner, for text-based types)
     |
     v
    Structure detection (StructureDetector / .tex chapters&sections / etc.)
     |
     v
    Normalization       (per-type metadata shaping)
     |
     v
    Chunking            (TextChunker, or type-specific: rule / entry / method)
     |
     v
    ProcessedChunk[]

Each step is its own small class so it can be tested and swapped
independently. `DocumentProcessor` is the single orchestrator that views/
services call — it owns a registry of {extension: extractor} and decides
how to route a file (or, for a .zip, each file inside it).

This module stays independent from Django views, the Agent, RAG,
embeddings, vector DB and LLM layers: it takes a file path + a
document_id and returns plain Python objects. Persisting the result into
`document_chunks` (see chatbot.models.DocumentChunk) is the caller's job
— see `ProcessedChunk.to_model_kwargs()` for the mapping, and the usage
example at the bottom of this file.

Dependencies (add to requirements.txt):
    pypdf>=4.0          # PDF text extraction
    python-docx>=1.1    # DOCX text extraction
    Pillow>=10.0         # optional: image dimensions/format; degrades
                         # gracefully to no metadata if not installed

Optional dependencies (each one degrades gracefully to a heuristic /
"not configured" state if not installed — nothing breaks without them):
    pdfplumber           # real PDF table extraction (PdfExtractor falls
                         # back to whitespace-heuristic tables without it)
    pytesseract          # powers PytesseractOCR (needs the tesseract-ocr
                         # system binary too); wire it in with
                         # DocumentProcessor(ocr_engine=PytesseractOCR())

No new dependency was added for .tex/.cls/.bib/.java: they are parsed with
the standard library (re) using hand-written, brace-depth-aware logic
where a simple regex would be unsafe (see BibExtractor._split_entries).
Where a real parser would meaningfully improve accuracy, that trade-off is
called out in the relevant class docstring (TexExtractor, JavaExtractor)
instead of silently adding the dependency — `pylatexenc` and `javalang`
are the natural upgrades if that accuracy is ever needed.
"""
from __future__ import annotations

import re
import tempfile
import uuid
import zipfile
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Any, Protocol

try:
    from pypdf import PdfReader
except ImportError:  # pragma: no cover - optional at import time
    PdfReader = None  # type: ignore[assignment,misc]

try:
    import docx  # python-docx
except ImportError:  # pragma: no cover - optional at import time
    docx = None  # type: ignore[assignment]

try:
    from PIL import Image
except ImportError:  # pragma: no cover - optional at import time
    Image = None  # type: ignore[assignment]

try:
    import pdfplumber
except ImportError:  # pragma: no cover - optional at import time
    pdfplumber = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Errors
# ---------------------------------------------------------------------------

class DocumentProcessingError(Exception):
    """Raised whenever a document (or a member inside a ZIP) cannot be
    extracted or processed."""


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------

@dataclass
class ExtractedPage:
    """Raw text extracted from one page (PDF) or section (DOCX/TXT), pre-clean."""

    index: int
    text: str


@dataclass
class StructuredBlock:
    """One paragraph or heading, tagged with the section it belongs to."""

    text: str
    heading: str | None
    is_heading: bool


@dataclass
class ProcessedChunk:
    """A single chunk produced from an uploaded document.

    Maps directly onto chatbot.models.DocumentChunk:
        chunk_id     -> DocumentChunk.id
        document_id  -> DocumentChunk.document_id
        chunk_index  -> DocumentChunk.chunk_index
        text         -> DocumentChunk.content
        metadata     -> not persisted by the current model; keep it around
                        for the embeddings/RAG step, or add a JSONField
                        later. Always carries `source_file` and
                        `file_type`; the rest (page, heading, chapter,
                        section, class_name, rule_type, ...) is filled in
                        only when relevant to that file type.
    """

    chunk_id: str
    document_id: str
    chunk_index: int
    text: str
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_model_kwargs(self) -> dict[str, Any]:
        """Kwargs ready for `DocumentChunk.objects.create(**kwargs)`."""
        return {
            "id": self.chunk_id,
            "document_id": self.document_id,
            "chunk_index": self.chunk_index,
            "content": self.text,
        }


# ---------------------------------------------------------------------------
# Shared text pipeline: cleaning, structure detection, chunking
# ---------------------------------------------------------------------------

class TextCleaner:
    """Normalizes whitespace and strips common extraction artifacts."""

    _MULTI_SPACE = re.compile(r"[ \t]+")
    _MULTI_BLANK_LINES = re.compile(r"\n{3,}")
    _HYPHEN_LINEBREAK = re.compile(r"(\w)-\n(\w)")  # "infor-\nmation" -> "information"
    _PAGE_NUMBER_LINE = re.compile(r"^\s*\d{1,4}\s*$")

    def clean(self, text: str) -> str:
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        text = self._HYPHEN_LINEBREAK.sub(r"\1\2", text)

        lines: list[str] = []
        for raw_line in text.split("\n"):
            line = self._MULTI_SPACE.sub(" ", raw_line).strip()
            if self._PAGE_NUMBER_LINE.match(line):
                continue  # drop bare page-number lines left over by PDF extraction
            lines.append(line)

        text = "\n".join(lines)
        text = self._MULTI_BLANK_LINES.sub("\n\n", text)
        return text.strip()


class StructureDetector:
    """Splits cleaned text into blocks and tracks the current heading.

    Heuristic, not a full layout parser — good enough for course PDFs and
    Word documents:
      - explicit "#" markers (from DOCX heading styles or Markdown source),
      - short lines (< 80 chars) with no ending punctuation that look like
        titles: numbered ("1.2 Introduction"), ALL CAPS, or Title Case.
    """

    _NUMBERED_HEADING = re.compile(r"^\d+(\.\d+)*\.?\s+\S")

    def detect(self, text: str) -> list[StructuredBlock]:
        blocks: list[StructuredBlock] = []
        current_heading: str | None = None

        for para in (p.strip() for p in text.split("\n\n")):
            if not para:
                continue
            first_line = para.split("\n", 1)[0]
            if self._looks_like_heading(first_line):
                heading_text = first_line.lstrip("#").strip()
                current_heading = heading_text
                blocks.append(
                    StructuredBlock(text=heading_text, heading=current_heading, is_heading=True)
                )
                remainder = para[len(first_line):].strip()
                if remainder:
                    blocks.append(
                        StructuredBlock(text=remainder, heading=current_heading, is_heading=False)
                    )
            else:
                blocks.append(
                    StructuredBlock(text=para, heading=current_heading, is_heading=False)
                )
        return blocks

    def _looks_like_heading(self, line: str) -> bool:
        if line.startswith("#"):
            return True
        if not line or len(line) > 80:
            return False
        if line.endswith((".", ",", ";", ":")):
            return False
        if self._NUMBERED_HEADING.match(line):
            return True

        letters = [c for c in line if c.isalpha()]
        if letters and sum(c.isupper() for c in letters) / len(letters) > 0.6:
            return True

        words = [w for w in line.split() if w]
        if words and sum(w[:1].isupper() for w in words) / len(words) > 0.7:
            return True

        return False


class TextChunker:
    """Splits structured blocks into overlapping chunks of ~chunk_size chars.

    A chunk never splits a sentence when avoidable, and keeps the heading of
    the section it came from so retrieval can cite "Section X, page Y".

    Called once per "scope" (a page, a LaTeX section, a Java method, ...):
    the buffer is local to each call, so calling `.chunk()` separately per
    scope naturally keeps chunk boundaries aligned with that scope instead
    of bleeding across sections.
    """

    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 150):
        if chunk_overlap >= chunk_size:
            raise ValueError("chunk_overlap must be smaller than chunk_size")
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk(self, blocks: list[StructuredBlock]) -> list[tuple[str, str | None]]:
        """Returns a list of (chunk_text, heading) tuples."""
        chunks: list[tuple[str, str | None]] = []
        buffer = ""
        buffer_heading: str | None = None

        def flush() -> None:
            nonlocal buffer
            text = buffer.strip()
            if text:
                chunks.append((text, buffer_heading))
            buffer = ""

        for block in blocks:
            if block.is_heading:
                continue  # heading text becomes metadata, not duplicated content
            for sentence in self._split_sentences(block.text):
                candidate = f"{buffer} {sentence}".strip() if buffer else sentence
                if len(candidate) <= self.chunk_size:
                    buffer = candidate
                    buffer_heading = block.heading
                else:
                    # BUGFIX: the overlap tail must be captured from the
                    # *current* buffer before flush() clears it. The
                    # previous version called flush() first, so `buffer`
                    # was already "" by the time overlap_tail was read —
                    # meaning no chunk ever actually carried its overlap
                    # forward into the next one.
                    overlap_tail = buffer[-self.chunk_overlap:] if buffer else ""
                    flush()
                    buffer = f"{overlap_tail} {sentence}".strip()
                    buffer_heading = block.heading
        flush()
        return chunks

    @staticmethod
    def _split_sentences(text: str) -> list[str]:
        # Simple sentence splitter — good enough without pulling in nltk/spacy.
        parts = re.split(r"(?<=[.!?])\s+(?=[A-ZÀ-Ý0-9])", text)
        return [p.strip() for p in parts if p.strip()]


# ---------------------------------------------------------------------------
# Extractor protocol — every per-file-type extractor implements this shape
# ---------------------------------------------------------------------------

class Extractor(Protocol):
    file_type: str

    def extract(
        self, file_path: Path, document_id: str, chunk_index_start: int = 0
    ) -> list[ProcessedChunk]: ...


# ---------------------------------------------------------------------------
# PDF / DOCX / TXT / MD — share one extract->clean->structure->chunk pipeline
# ---------------------------------------------------------------------------

class GenericTextExtractor:
    """Shared pipeline for page/section-based text formats.

    Subclasses only implement `_extract_pages`; cleaning, heading
    detection, chunking and metadata shaping are identical for
    PDF / DOCX / TXT / MD, so they live here once.
    """

    file_type = "text"

    def __init__(
        self,
        cleaner: TextCleaner | None = None,
        structure_detector: StructureDetector | None = None,
        chunker: TextChunker | None = None,
    ):
        self.cleaner = cleaner or TextCleaner()
        self.structure_detector = structure_detector or StructureDetector()
        self.chunker = chunker or TextChunker(chunk_size=1000, chunk_overlap=150)

    def _extract_pages(self, file_path: Path) -> list[ExtractedPage]:
        raise NotImplementedError

    def extract(
        self, file_path: Path, document_id: str, chunk_index_start: int = 0
    ) -> list[ProcessedChunk]:
        pages = self._extract_pages(file_path)

        chunks: list[ProcessedChunk] = []
        chunk_index = chunk_index_start
        for page in pages:
            cleaned = self.cleaner.clean(page.text)
            if not cleaned:
                continue
            blocks = self.structure_detector.detect(cleaned)
            for chunk_text, heading in self.chunker.chunk(blocks):
                chunks.append(
                    ProcessedChunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        chunk_index=chunk_index,
                        text=chunk_text,
                        metadata={
                            "source_file": file_path.name,
                            "file_type": self.file_type,
                            "page": page.index,
                            "heading": heading,
                            "char_count": len(chunk_text),
                        },
                    )
                )
                chunk_index += 1

        if not chunks:
            raise DocumentProcessingError(f"No extractable text found in {file_path.name}")
        return chunks


class PdfExtractor(GenericTextExtractor):
    file_type = "pdf"

    # A run of 2+ spaces between tokens, at least twice on the line, looks
    # like column alignment left over from a PDF table.
    _TABLE_ROW_RE = re.compile(r"\S+(?:\s{2,}\S+){1,}")

    def _extract_pages(self, file_path: Path) -> list[ExtractedPage]:
        if PdfReader is None:
            raise DocumentProcessingError("pypdf is not installed. Run: pip install pypdf")
        try:
            reader = PdfReader(str(file_path))
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller
            raise DocumentProcessingError(f"Could not open PDF: {exc}") from exc

        # If pdfplumber is available, use its real table detection instead
        # of the whitespace heuristic below, page by page. This is kept
        # entirely optional: without pdfplumber installed, behavior is
        # unchanged (heuristic-only, as before).
        plumber_tables_by_page = self._extract_tables_with_pdfplumber(file_path)

        pages: list[ExtractedPage] = []
        for i, page in enumerate(reader.pages):
            try:
                text = page.extract_text() or ""
            except Exception:  # noqa: BLE001 - a bad page must not kill the rest
                text = ""

            page_num = i + 1
            real_tables = plumber_tables_by_page.get(page_num)
            if real_tables:
                # Real tables found -> append them as clean rows instead of
                # relying on whitespace-column guessing for this page.
                text = text + "\n\n" + "\n".join(real_tables)
            else:
                text = self._mark_tables(text)

            pages.append(ExtractedPage(index=page_num, text=text))
        return pages

    def _extract_tables_with_pdfplumber(self, file_path: Path) -> dict[int, list[str]]:
        """Returns {page_number: [rendered_row, ...]} for pages where
        pdfplumber found at least one real table. Best-effort: any failure
        here (corrupt page, unsupported layout, pdfplumber not installed)
        simply means we fall back to `_mark_tables`'s heuristic — it never
        raises, since table extraction is an enhancement, not a
        requirement for text extraction to succeed."""
        if pdfplumber is None:
            return {}
        results: dict[int, list[str]] = {}
        try:
            with pdfplumber.open(str(file_path)) as pdf:
                for i, page in enumerate(pdf.pages):
                    try:
                        tables = page.extract_tables()
                    except Exception:  # noqa: BLE001
                        continue
                    rendered: list[str] = []
                    for table in tables:
                        for row in table:
                            cells = [(c or "").strip() for c in row]
                            if any(cells):
                                rendered.append(" | ".join(cells))
                    if rendered:
                        results[i + 1] = rendered
        except Exception:  # noqa: BLE001 - never let table extraction break text extraction
            return {}
        return results

    def _mark_tables(self, text: str) -> str:
        """Heuristically preserves table-like rows as `cell | cell | cell`.

        Fallback used only when pdfplumber is unavailable or found no real
        tables on this page. pypdf itself exposes no table structure, so
        this only keeps column alignment visible instead of losing it to
        whitespace collapsing in TextCleaner — it is not accurate table
        extraction. Install `pdfplumber` for real `page.extract_tables()`
        results (wired in above automatically when present).
        """
        lines = []
        for line in text.split("\n"):
            if "  " in line and self._TABLE_ROW_RE.search(line):
                cells = [c for c in re.split(r"\s{2,}", line.strip()) if c]
                if len(cells) > 1:
                    line = " | ".join(cells)
            lines.append(line)
        return "\n".join(lines)


class DocxExtractor(GenericTextExtractor):
    file_type = "docx"

    def _extract_pages(self, file_path: Path) -> list[ExtractedPage]:
        if docx is None:
            raise DocumentProcessingError(
                "python-docx is not installed. Run: pip install python-docx"
            )
        try:
            document = docx.Document(str(file_path))
        except Exception as exc:  # noqa: BLE001
            raise DocumentProcessingError(f"Could not open DOCX: {exc}") from exc

        # DOCX has no reliable native "page" concept: true page boundaries
        # depend on rendering (font, margins, printer driver) and are not
        # stored in the file. What *is* stored is any explicit hard page
        # break the author inserted (Ctrl+Enter), as <w:br w:type="page"/>.
        # We use those as page boundaries — an honest floor on the real
        # page count, not an exact page map. Text that wraps to a new page
        # naturally (no manual break) will still be reported under the
        # previous page's number.
        pages_lines: list[list[str]] = [[]]
        for para in document.paragraphs:
            text = para.text.strip()
            if text:
                style_name = (para.style.name if para.style else "") or ""
                if style_name.lower().startswith("heading"):
                    digits = "".join(c for c in style_name if c.isdigit()) or "1"
                    level = min(int(digits), 6)
                    pages_lines[-1].append(f"{'#' * level} {text}")
                else:
                    pages_lines[-1].append(text)
            if self._has_page_break(para):
                pages_lines.append([])

        for table in document.tables:
            for row in table.rows:
                cells = [cell.text.strip() for cell in row.cells]
                if any(cells):
                    pages_lines[-1].append(" | ".join(cells))

        pages = [
            ExtractedPage(index=i + 1, text="\n".join(lines))
            for i, lines in enumerate(pages_lines)
            if lines
        ]
        return pages or [ExtractedPage(index=1, text="")]

    @staticmethod
    def _has_page_break(paragraph) -> bool:
        """True if this paragraph contains an explicit hard page break.

        python-docx has no high-level API for this, so we check the
        paragraph's raw XML for a `<w:br w:type="page"/>` run — the tag
        Word uses for a manual page break. Safe to call on any paragraph;
        any XML-access failure is treated as "no break found".
        """
        try:
            xml = paragraph._p.xml  # noqa: SLF001 - no public API for this
        except Exception:  # noqa: BLE001
            return False
        return 'type="page"' in xml or "type='page'" in xml


class PlainTextExtractor(GenericTextExtractor):
    """Handles both .txt and .md — pass `file_type` to distinguish them."""

    def __init__(self, file_type: str = "txt", **kwargs):
        super().__init__(**kwargs)
        self.file_type = file_type

    def _extract_pages(self, file_path: Path) -> list[ExtractedPage]:
        try:
            text = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            raise DocumentProcessingError(f"Could not read text file: {exc}") from exc
        return [ExtractedPage(index=1, text=text)]


# ---------------------------------------------------------------------------
# LaTeX (.tex) — chapter/section-aware
# ---------------------------------------------------------------------------

_TEX_HEADING_RE = re.compile(r"\\(chapter|section|subsection|subsubsection)\*?\{([^{}]*)\}")
_TEX_COMMENT_RE = re.compile(r"(?<!\\)%.*")
_TEX_LABEL_RE = re.compile(r"\\label\{[^}]*\}")
_TEX_REF_RE = re.compile(r"\\(?:ref|cite|eqref|autoref)\{([^}]*)\}")
_TEX_INLINE_FORMAT_RE = re.compile(r"\\(?:textbf|textit|emph|underline|texttt)\{([^{}]*)\}")
_TEX_BEGIN_DOCUMENT_RE = re.compile(r"\\begin\{document\}")
_TEX_END_DOCUMENT_RE = re.compile(r"\\end\{document\}")


class TexExtractor:
    """Structure-aware extractor for LaTeX (.tex) source files.

    Not a full LaTeX parser — that would need an external dependency such
    as `pylatexenc` or `TexSoup`. This uses a regex-based scan for the
    sectioning commands (\\chapter, \\section, \\subsection,
    \\subsubsection), which covers the vast majority of thesis/report
    documents, and strips comments, \\label{}, and a few inline formatting
    commands from the body text so chunks stay readable. Other commands
    (environments, math, \\includegraphics, ...) are left as-is: still
    useful context for retrieval, just not further parsed. If richer
    parsing is needed later, `pylatexenc.latexwalker` is the natural
    upgrade — it is pure Python (no LaTeX installation required).
    """

    file_type = "tex"

    def __init__(self, chunker: TextChunker | None = None, cleaner: TextCleaner | None = None):
        self.cleaner = cleaner or TextCleaner()
        self.chunker = chunker or TextChunker(chunk_size=1000, chunk_overlap=150)

    def extract(
        self, file_path: Path, document_id: str, chunk_index_start: int = 0
    ) -> list[ProcessedChunk]:
        try:
            raw = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            raise DocumentProcessingError(f"Could not read .tex file: {exc}") from exc

        # Only the body matters for retrieval; the preamble (\documentclass,
        # \usepackage, \newcommand…) is formatting setup, not content — and
        # is exactly what ClsExtractor handles for the .cls file itself.
        body_match = _TEX_BEGIN_DOCUMENT_RE.search(raw)
        body = raw[body_match.end():] if body_match else raw
        end_match = _TEX_END_DOCUMENT_RE.search(body)
        if end_match:
            body = body[: end_match.start()]

        segments = self._split_by_heading(body)

        chunks: list[ProcessedChunk] = []
        chunk_index = chunk_index_start
        for chapter, section, subsection, heading, text in segments:
            cleaned = self.cleaner.clean(self._clean_latex(text))
            if not cleaned:
                continue
            block = StructuredBlock(text=cleaned, heading=heading, is_heading=False)
            for chunk_text, _heading in self.chunker.chunk([block]):
                chunks.append(
                    ProcessedChunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        chunk_index=chunk_index,
                        text=chunk_text,
                        metadata={
                            "source_file": file_path.name,
                            "file_type": self.file_type,
                            "chapter": chapter,
                            "section": section,
                            "subsection": subsection,
                            "heading": heading,
                            "char_count": len(chunk_text),
                        },
                    )
                )
                chunk_index += 1

        if not chunks:
            raise DocumentProcessingError(f"No extractable text found in {file_path.name}")
        return chunks

    def _split_by_heading(
        self, body: str
    ) -> list[tuple[str | None, str | None, str | None, str | None, str]]:
        """Walks \\chapter/\\section/\\subsection/\\subsubsection commands,
        tracking the current chapter/section/subsection state, and returns
        one (chapter, section, subsection, heading, content) tuple per
        segment of body text between two headings."""
        matches = list(_TEX_HEADING_RE.finditer(body))
        segments: list[tuple[str | None, str | None, str | None, str | None, str]] = []
        chapter = section = subsection = None

        first_start = matches[0].start() if matches else len(body)
        intro = body[:first_start]
        if intro.strip():
            segments.append((chapter, section, subsection, None, intro))

        for i, m in enumerate(matches):
            level_name, title = m.group(1), m.group(2).strip()
            if level_name == "chapter":
                chapter, section, subsection = title, None, None
            elif level_name == "section":
                section, subsection = title, None
            elif level_name == "subsection":
                subsection = title
            # subsubsection doesn't get its own tracked field, only `heading`
            heading = title

            start = m.end()
            end = matches[i + 1].start() if i + 1 < len(matches) else len(body)
            segments.append((chapter, section, subsection, heading, body[start:end]))

        return segments

    def _clean_latex(self, text: str) -> str:
        text = _TEX_COMMENT_RE.sub("", text)
        text = _TEX_LABEL_RE.sub("", text)
        text = _TEX_REF_RE.sub(lambda m: m.group(1), text)
        # Unwrap simple formatting commands, keeping only their argument
        # text; repeat until stable to handle nested formatting.
        previous = None
        while previous != text:
            previous = text
            text = _TEX_INLINE_FORMAT_RE.sub(lambda m: m.group(1), text)
        return text


# ---------------------------------------------------------------------------
# LaTeX class (.cls) — structured formatting rules
# ---------------------------------------------------------------------------

# (rule_type, pattern). `pattern` must have its *value* in the last group.
_CLS_RULE_PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    ("margin", re.compile(r"\\geometry\{([^}]*)\}")),
    ("margin", re.compile(r"\\(?:oddsidemargin|evensidemargin|topmargin|marginparwidth)\s*=?\s*([\-\d.]+\s*\w+)")),
    ("page_layout", re.compile(r"\\(?:textwidth|textheight|paperwidth|paperheight)\s*=?\s*([\-\d.]+\s*\w+)")),
    ("spacing", re.compile(r"\\(?:linespread|parskip|parindent|baselineskip)\s*\{?([\-\d.]+\s*\w*)\}?")),
    ("font", re.compile(r"\\(?:setmainfont|setsansfont|setmonofont)\{([^}]*)\}")),
    ("font", re.compile(r"\\renewcommand\{\\(?:rmdefault|sfdefault|ttdefault)\}\{([^}]*)\}")),
    ("section_format", re.compile(r"(\\titleformat\{\\(?:chapter|section|subsection)\}.*)")),
    ("document_structure", re.compile(r"\\newenvironment\{([^}]*)\}")),
    ("document_structure", re.compile(r"\\newtheorem\{([^}]*)\}")),
    ("package", re.compile(r"\\usepackage(?:\[[^\]]*\])?\{([^}]*)\}")),
]


class ClsExtractor:
    """Extracts structured formatting rules from a LaTeX class (.cls) file.

    A .cls file is mostly macro plumbing that is useless for retrieval as
    raw text. Instead of dumping it, this pulls out the handful of
    construct categories that describe *document formatting rules* —
    margin, font, spacing, page layout, section formatting, packages,
    custom environments/theorems — the kind of thing worth answering "what
    margin does the template use?" from. Anything not matching a known
    category is left out on purpose (don't turn every implementation
    detail into an arbitrary chunk).
    """

    file_type = "cls"

    def extract(
        self, file_path: Path, document_id: str, chunk_index_start: int = 0
    ) -> list[ProcessedChunk]:
        try:
            raw = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            raise DocumentProcessingError(f"Could not read .cls file: {exc}") from exc

        chunks: list[ProcessedChunk] = []
        chunk_index = chunk_index_start
        packages: list[str] = []

        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("%"):
                continue
            for rule_type, pattern in _CLS_RULE_PATTERNS:
                match = pattern.search(line)
                if not match:
                    continue
                value = match.group(match.lastindex or 1).strip()
                if rule_type == "package":
                    # Collected separately below into one packages chunk,
                    # rather than one chunk per \usepackage line.
                    packages.extend(p.strip() for p in value.split(",") if p.strip())
                    break
                chunks.append(
                    ProcessedChunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        chunk_index=chunk_index,
                        text=line,
                        metadata={
                            "source_file": file_path.name,
                            "file_type": self.file_type,
                            "rule_type": rule_type,
                            "value": value,
                        },
                    )
                )
                chunk_index += 1
                break  # one rule category per line is enough

        if packages:
            unique_packages = sorted(set(packages))
            chunks.append(
                ProcessedChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=chunk_index,
                    text="Packages: " + ", ".join(unique_packages),
                    metadata={
                        "source_file": file_path.name,
                        "file_type": self.file_type,
                        "rule_type": "package",
                        "value": unique_packages,
                    },
                )
            )
            chunk_index += 1

        if not chunks:
            raise DocumentProcessingError(
                f"No recognizable formatting rules found in {file_path.name}"
            )
        return chunks


# ---------------------------------------------------------------------------
# BibTeX (.bib) — structured citation records
# ---------------------------------------------------------------------------

_BIB_KNOWN_FIELDS = (
    "author", "title", "year", "journal", "booktitle", "doi",
    "publisher", "volume", "number", "pages", "url",
)


class BibExtractor:
    """Parses BibTeX (.bib) entries into structured records.

    Hand-written with a brace-depth-aware scanner instead of a regex
    split, because BibTeX field values legitimately contain nested braces
    (e.g. a title with `{AI}` protected capitalization) that a naive
    comma/brace regex would break on. No external dependency (e.g.
    `bibtexparser`) is needed for this subset of the grammar — if BibTeX
    string macros (`@string`) or cross references (`crossref`) need to be
    resolved later, `bibtexparser` would be the natural upgrade.
    """

    file_type = "bib"

    def extract(
        self, file_path: Path, document_id: str, chunk_index_start: int = 0
    ) -> list[ProcessedChunk]:
        try:
            raw = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            raise DocumentProcessingError(f"Could not read .bib file: {exc}") from exc

        chunks: list[ProcessedChunk] = []
        chunk_index = chunk_index_start

        for entry_type, citation_key, fields_body in self._split_entries(raw):
            fields = self._parse_fields(fields_body)
            metadata: dict = {
                "source_file": file_path.name,
                "file_type": self.file_type,
                "citation_key": citation_key,
                "entry_type": entry_type,
            }
            for key in _BIB_KNOWN_FIELDS:
                if key in fields:
                    metadata[key] = fields[key]
            extra = {k: v for k, v in fields.items() if k not in _BIB_KNOWN_FIELDS}
            if extra:
                metadata["extra_fields"] = extra

            chunks.append(
                ProcessedChunk(
                    chunk_id=str(uuid.uuid4()),
                    document_id=document_id,
                    chunk_index=chunk_index,
                    text=self._summarize(citation_key, fields),
                    metadata=metadata,
                )
            )
            chunk_index += 1

        if not chunks:
            raise DocumentProcessingError(f"No BibTeX entries found in {file_path.name}")
        return chunks

    def _split_entries(self, raw: str) -> list[tuple[str, str, str]]:
        """Finds each `@type{key, field=..., ...}` block via brace counting."""
        entries: list[tuple[str, str, str]] = []
        i, n = 0, len(raw)
        while i < n:
            if raw[i] != "@":
                i += 1
                continue
            j = i + 1
            while j < n and raw[j] not in "{(":
                j += 1
            entry_type = raw[i + 1 : j].strip().lower()
            if j >= n:
                break
            if entry_type in ("comment", "string", "preamble"):
                i = j + 1
                continue

            open_char, close_char = raw[j], ("}" if raw[j] == "{" else ")")
            depth, k = 1, j + 1
            while k < n and depth > 0:
                if raw[k] == open_char:
                    depth += 1
                elif raw[k] == close_char:
                    depth -= 1
                k += 1
            body = raw[j + 1 : k - 1]

            comma = body.find(",")
            citation_key = (body[:comma] if comma != -1 else body).strip()
            fields_body = body[comma + 1 :] if comma != -1 else ""
            if citation_key:
                entries.append((entry_type, citation_key, fields_body))
            i = k
        return entries

    def _parse_fields(self, body: str) -> dict[str, str]:
        fields: dict[str, str] = {}
        for raw_field in self._split_top_level(body, ","):
            if "=" not in raw_field:
                continue
            key, _, value = raw_field.partition("=")
            key = key.strip().lower()
            value = value.strip().strip(",").strip().strip("{}").strip('"')
            value = " ".join(value.split())
            if key and value:
                fields[key] = value
        return fields

    @staticmethod
    def _split_top_level(s: str, sep: str) -> list[str]:
        """Splits on `sep` only outside any {..} or (..) nesting."""
        parts: list[str] = []
        depth = 0
        current: list[str] = []
        for ch in s:
            if ch in "{(":
                depth += 1
            elif ch in "})":
                depth = max(0, depth - 1)
            if ch == sep and depth == 0:
                parts.append("".join(current))
                current = []
            else:
                current.append(ch)
        if current:
            parts.append("".join(current))
        return parts

    @staticmethod
    def _summarize(citation_key: str, fields: dict[str, str]) -> str:
        author = fields.get("author", "Unknown author")
        title = fields.get("title", citation_key)
        year = fields.get("year", "n.d.")
        venue = fields.get("journal") or fields.get("booktitle") or ""
        summary = f"{author} ({year}). {title}."
        if venue:
            summary += f" {venue}."
        return summary


# ---------------------------------------------------------------------------
# Java (.java) — class/method-aware
# ---------------------------------------------------------------------------

_JAVA_LINE_COMMENT_RE = re.compile(r"//.*")
_JAVA_BLOCK_COMMENT_RE = re.compile(r"/\*.*?\*/", re.DOTALL)
_JAVA_PACKAGE_RE = re.compile(r"^\s*package\s+([\w.]+)\s*;", re.MULTILINE)
_JAVA_IMPORT_RE = re.compile(r"^\s*import\s+(?:static\s+)?([\w.\*]+)\s*;", re.MULTILINE)
_JAVA_TYPE_DECL_RE = re.compile(
    r"(?P<vis>public|private|protected)?\s*"
    r"(?:(?:abstract|final|static)\s+)*"
    r"(?P<kind>class|interface|enum)\s+"
    r"(?P<name>\w+)"
    r"(?:\s+extends\s+[\w<>,\s]+)?"
    r"(?:\s+implements\s+[\w<>,\s]+)?"
    r"\s*\{"
)
# Anchored to line-start (`^\s*`, MULTILINE) so the optional `vis` group
# only ever matches when "public"/"private"/"protected" is literally the
# next token — without the anchor, the non-greedy return-type group can
# swallow the visibility keyword instead of the regex engine backtracking
# to try the later position where it's actually written.
_JAVA_METHOD_RE = re.compile(
    r"^\s*(?P<vis>public|private|protected)?\s*"
    r"(?:(?:static|final|abstract|synchronized)\s+)*"
    r"(?:[\w<>\[\],\s]+?\s+)"
    r"(?P<name>\w+)\s*"
    r"\((?P<params>[^)]*)\)\s*"
    r"(?:throws\s+[\w.,\s]+)?\s*\{",
    re.MULTILINE,
)
_JAVA_FIELD_RE = re.compile(
    r"^\s*(?P<vis>public|private|protected)?\s*"
    r"(?:(?:static|final)\s+)*"
    r"(?P<type>[\w<>\[\],.]+)\s+"
    r"(?P<name>\w+)\s*(?:=.*)?;\s*$",
    re.MULTILINE,
)


class JavaExtractor:
    """Structure-aware extractor for Java (.java) source files.

    Uses regular expressions plus brace-depth matching instead of a real
    parser. A proper AST — e.g. via the pure-Python `javalang` package
    (`pip install javalang`, no JDK/native build required) — would resolve
    generics, nested/anonymous classes and annotations far more reliably.
    It is not added now to avoid a new dependency for an MVP heuristic that
    already covers the common case (one top-level class with fields and
    methods); if accuracy on more complex files becomes an issue,
    `javalang` is the natural upgrade and would slot in behind the same
    `extract()` signature.

    Chunking here is code-aware, not character-based: one chunk for the
    class declaration + fields, and one chunk per method (its full body,
    via brace matching) — falling back to the generic sentence chunker
    only if a single method body is unusually large.
    """

    file_type = "java"

    def __init__(self, chunker: TextChunker | None = None):
        self.chunker = chunker or TextChunker(chunk_size=1500, chunk_overlap=100)

    def extract(
        self, file_path: Path, document_id: str, chunk_index_start: int = 0
    ) -> list[ProcessedChunk]:
        try:
            raw = file_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:  # noqa: BLE001
            raise DocumentProcessingError(f"Could not read .java file: {exc}") from exc

        code = self._strip_comments(raw)
        package = self._find_package(code)
        imports = self._find_imports(code)

        type_match = _JAVA_TYPE_DECL_RE.search(code)
        if type_match is None:
            raise DocumentProcessingError(
                f"No class/interface/enum declaration found in {file_path.name}"
            )

        class_name = type_match.group("name")
        class_vis = (type_match.group("vis") or "package-private").strip()
        class_body_start = type_match.end()
        class_body_end = self._matching_brace(code, class_body_start - 1)
        class_body = (
            code[class_body_start:class_body_end]
            if class_body_end != -1
            else code[class_body_start:]
        )

        chunks: list[ProcessedChunk] = []
        chunk_index = chunk_index_start

        # 1) Class declaration + package/imports + fields, as one chunk.
        fields = self._find_fields(class_body)
        header_lines = [f"package {package};" if package else "", f"class {class_name}"]
        if fields:
            header_lines.append("Fields: " + ", ".join(f"{v} {t} {n}" for v, t, n in fields))
        chunks.append(
            ProcessedChunk(
                chunk_id=str(uuid.uuid4()),
                document_id=document_id,
                chunk_index=chunk_index,
                text="\n".join(line for line in header_lines if line),
                metadata={
                    "source_file": file_path.name,
                    "file_type": self.file_type,
                    "package": package,
                    "imports": imports,
                    "class_name": class_name,
                    "visibility": class_vis,
                    "content_type": "class_declaration",
                },
            )
        )
        chunk_index += 1

        # 2) One chunk per method — boundaries are method bodies, not
        #    arbitrary character counts.
        for method_match in _JAVA_METHOD_RE.finditer(class_body):
            name = method_match.group("name")
            vis = (method_match.group("vis") or "package-private").strip()
            body_start = method_match.end()
            body_end = self._matching_brace(class_body, body_start - 1)
            if body_end == -1:
                continue
            method_text = class_body[method_match.start():body_end].strip()

            pieces = [method_text]
            if len(method_text) > self.chunker.chunk_size:
                block = StructuredBlock(text=method_text, heading=None, is_heading=False)
                pieces = [piece for piece, _ in self.chunker.chunk([block])]

            for piece in pieces:
                chunks.append(
                    ProcessedChunk(
                        chunk_id=str(uuid.uuid4()),
                        document_id=document_id,
                        chunk_index=chunk_index,
                        text=piece,
                        metadata={
                            "source_file": file_path.name,
                            "file_type": self.file_type,
                            "package": package,
                            "class_name": class_name,
                            "method_name": name,
                            "visibility": vis,
                            "content_type": "method",
                        },
                    )
                )
                chunk_index += 1

        return chunks

    def _strip_comments(self, code: str) -> str:
        code = _JAVA_BLOCK_COMMENT_RE.sub("", code)
        code = _JAVA_LINE_COMMENT_RE.sub("", code)
        return code

    def _find_package(self, code: str) -> str | None:
        m = _JAVA_PACKAGE_RE.search(code)
        return m.group(1) if m else None

    def _find_imports(self, code: str) -> list[str]:
        return [m.group(1) for m in _JAVA_IMPORT_RE.finditer(code)]

    def _find_fields(self, class_body: str) -> list[tuple[str, str, str]]:
        """Best-effort: may also catch local variable declarations inside
        method bodies that happen to match the same shape. Acceptable for
        an MVP heuristic — a real parser (see class docstring) would not
        have this limitation."""
        fields = []
        for m in _JAVA_FIELD_RE.finditer(class_body):
            vis = (m.group("vis") or "package-private").strip()
            fields.append((vis, m.group("type").strip(), m.group("name")))
        return fields

    @staticmethod
    def _matching_brace(code: str, open_brace_index: int) -> int:
        """Returns the index just past the `}` matching the `{` at
        `open_brace_index`, or -1 if unbalanced."""
        depth = 0
        for idx in range(open_brace_index, len(code)):
            if code[idx] == "{":
                depth += 1
            elif code[idx] == "}":
                depth -= 1
                if depth == 0:
                    return idx + 1
        return -1


# ---------------------------------------------------------------------------
# Images (.png / .jpg / .jpeg) — extensible OCR/Vision abstraction
# ---------------------------------------------------------------------------

class OCREngine(Protocol):
    """Pluggable text-extraction backend for images."""

    def extract_text(self, file_path: Path) -> str: ...


class VisionDescriber(Protocol):
    """Pluggable backend for describing diagrams/figures in an image.

    Same idea as OCREngine: a future Vision/LLM-based describer implements
    this Protocol and gets injected — DocumentProcessor never imports a
    Vision API or LLM client directly (that logic belongs to a layer
    outside document processing).
    """

    def describe(self, file_path: Path) -> str: ...


class PytesseractOCR:
    """Ready-to-use OCREngine backed by pytesseract + Pillow.

    This is the concrete implementation the ImageExtractor docstring used
    to only sketch as a future example — it now actually exists. It still
    requires two things this project does not install by default:
      - the `pytesseract` pip package, and
      - the `tesseract-ocr` system binary (an OS-level install, e.g.
        `apt-get install tesseract-ocr` — not something pip can provide).
    Both are checked lazily, only when `extract_text` is actually called,
    so simply importing this class never fails.

    Wire it in with:
        DocumentProcessor(ocr_engine=PytesseractOCR())
    """

    def __init__(self, lang: str = "eng"):
        self.lang = lang

    def extract_text(self, file_path: Path) -> str:
        try:
            import pytesseract
        except ImportError as exc:
            raise DocumentProcessingError(
                "pytesseract is not installed. Run: pip install pytesseract "
                "(and install the tesseract-ocr system binary)."
            ) from exc
        if Image is None:
            raise DocumentProcessingError("Pillow is not installed. Run: pip install Pillow")
        try:
            with Image.open(file_path) as img:
                return pytesseract.image_to_string(img, lang=self.lang)
        except Exception as exc:  # noqa: BLE001 - surfaced to the caller
            raise DocumentProcessingError(f"OCR failed for {file_path.name}: {exc}") from exc


class ImageExtractor:
    """Extensible extractor for .png / .jpg / .jpeg files.

    Today: records basic image metadata (dimensions, format), and OCR
    text *if* an OCREngine is supplied (e.g. `PytesseractOCR()`), without
    ever pretending to have read image content it cannot access.

    Tomorrow: plug in a VisionDescriber implementation for
    diagrams/figures — the surrounding pipeline (DocumentProcessor,
    chunking, metadata shape) does not change.
    """

    file_type = "image"

    def __init__(
        self,
        ocr_engine: OCREngine | None = None,
        vision_describer: VisionDescriber | None = None,
    ):
        self.ocr_engine = ocr_engine
        self.vision_describer = vision_describer

    def extract(
        self, file_path: Path, document_id: str, chunk_index_start: int = 0
    ) -> list[ProcessedChunk]:
        width = height = None
        image_format = file_path.suffix.lstrip(".").lower()
        if Image is not None:
            try:
                with Image.open(file_path) as img:
                    width, height = img.size
                    image_format = (img.format or image_format).lower()
            except Exception:  # noqa: BLE001 - metadata is best-effort
                pass

        ocr_text, ocr_status = "", "not_configured"
        if self.ocr_engine is not None:
            try:
                ocr_text = self.ocr_engine.extract_text(file_path).strip()
                ocr_status = "extracted" if ocr_text else "no_text_found"
            except Exception as exc:  # noqa: BLE001
                ocr_status = f"failed: {exc}"

        vision_description, vision_status = "", "not_configured"
        if self.vision_describer is not None:
            try:
                vision_description = self.vision_describer.describe(file_path).strip()
                vision_status = "described" if vision_description else "no_description"
            except Exception as exc:  # noqa: BLE001
                vision_status = f"failed: {exc}"

        text = ocr_text or vision_description or (
            f"[Image '{file_path.name}' — no OCR/Vision engine configured. "
            "Register an OCREngine (e.g. PytesseractOCR()) or a "
            "VisionDescriber on DocumentProcessor to make this image's "
            "content retrievable.]"
        )

        chunk = ProcessedChunk(
            chunk_id=str(uuid.uuid4()),
            document_id=document_id,
            chunk_index=chunk_index_start,
            text=text,
            metadata={
                "source_file": file_path.name,
                "file_type": self.file_type,
                "image_format": image_format,
                "width": width,
                "height": height,
                "ocr_status": ocr_status,
                "vision_status": vision_status,
            },
        )
        return [chunk]


# ---------------------------------------------------------------------------
# ZIP security — extraction is the only place a hostile file gets touched
# ---------------------------------------------------------------------------

MAX_ZIP_ENTRIES = 500
MAX_SINGLE_FILE_BYTES = 50 * 1024 * 1024          # matches the upload limit
MAX_TOTAL_UNCOMPRESSED_BYTES = 200 * 1024 * 1024  # 200 MB extracted, total
MAX_COMPRESSION_RATIO = 100                        # uncompressed / compressed


@dataclass
class ExtractedEntry:
    """One safely-extracted member of a ZIP archive."""

    relative_path: str   # original filename inside the zip, e.g. "chapter1.tex"
    absolute_path: Path  # where it was written on disk (inside dest_dir)


def secure_extract_zip(
    zip_path: Path, dest_dir: Path, allowed_extensions: set[str]
) -> list[ExtractedEntry]:
    """Safely extracts the supported members of `zip_path` into `dest_dir`.

    Only the standard library is used (zipfile, pathlib). Threat model
    covered:
      - absolute paths / drive letters,
      - `../` path traversal (and any entry that resolves outside
        `dest_dir` once normalized),
      - per-file and total uncompressed size limits,
      - compressed/uncompressed ratio limit (zip-bomb guard),
      - entry count limit,
      - unsupported/non-allowlisted file types (skipped — an allowlist is
        safer than trying to blocklist every executable extension).

    Nothing inside the archive is ever executed: files are only read as
    bytes via `ZipFile.open()` and written to `dest_dir`.

    A member outside `allowed_extensions` is silently skipped (not a
    security issue — just nothing this pipeline knows how to process). A
    member that looks malicious (traversal, absolute path, oversized, or
    an archive that trips the entry/size/ratio caps) aborts the whole
    extraction with DocumentProcessingError, rather than skipping just
    that one entry.
    """
    dest_root = dest_dir.resolve()

    try:
        zf = zipfile.ZipFile(zip_path)
    except zipfile.BadZipFile as exc:
        raise DocumentProcessingError(f"Not a valid ZIP file: {exc}") from exc

    entries: list[ExtractedEntry] = []
    total_uncompressed = 0

    with zf:
        infos = zf.infolist()
        if len(infos) > MAX_ZIP_ENTRIES:
            raise DocumentProcessingError(
                f"ZIP has too many entries ({len(infos)} > {MAX_ZIP_ENTRIES})."
            )

        for info in infos:
            if info.is_dir():
                continue

            name = info.filename

            # --- path safety ---------------------------------------------
            if name.startswith("/") or name.startswith("\\") or ":" in name:
                raise DocumentProcessingError(f"Unsafe path in ZIP entry: {name!r}")
            if ".." in PurePosixPath(name).parts:
                raise DocumentProcessingError(
                    f"Path traversal attempt in ZIP entry: {name!r}"
                )

            target = (dest_root / name).resolve()
            if not target.is_relative_to(dest_root):
                raise DocumentProcessingError(
                    f"ZIP entry escapes the extraction directory: {name!r}"
                )

            # --- size / zip-bomb guards ------------------------------------
            if info.file_size > MAX_SINGLE_FILE_BYTES:
                raise DocumentProcessingError(
                    f"ZIP entry {name!r} exceeds the "
                    f"{MAX_SINGLE_FILE_BYTES // (1024 * 1024)} MB per-file limit."
                )

            if info.compress_size > 0:
                ratio = info.file_size / info.compress_size
                if ratio > MAX_COMPRESSION_RATIO:
                    raise DocumentProcessingError(
                        f"ZIP entry {name!r} has a suspicious compression ratio "
                        f"({ratio:.0f}:1) — refusing to extract (possible zip bomb)."
                    )

            total_uncompressed += info.file_size
            if total_uncompressed > MAX_TOTAL_UNCOMPRESSED_BYTES:
                raise DocumentProcessingError(
                    "ZIP exceeds the total uncompressed size limit "
                    f"({MAX_TOTAL_UNCOMPRESSED_BYTES // (1024 * 1024)} MB)."
                )

            # --- allowlist: only extract file types we know how to process -
            ext = "." + name.rsplit(".", 1)[-1].lower() if "." in name else ""
            if ext not in allowed_extensions:
                continue

            target.parent.mkdir(parents=True, exist_ok=True)
            with zf.open(info) as source, open(target, "wb") as out:
                out.write(source.read())

            entries.append(ExtractedEntry(relative_path=name, absolute_path=target))

    return entries


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

class DocumentProcessor:
    """Extracts, cleans, structures and chunks a document end to end.

    Dispatches to a per-extension extractor (see `_build_registry`).
    `.zip` is handled specially: it is securely unpacked and each
    supported member inside it is routed to its own extractor, with the
    *internal* filename preserved as `source_file` in the resulting
    chunks' metadata (never the archive's own name).
    """

    def __init__(
        self,
        ocr_engine: OCREngine | None = None,
        vision_describer: VisionDescriber | None = None,
    ):
        self._registry: dict[str, Extractor] = self._build_registry(
            ocr_engine=ocr_engine, vision_describer=vision_describer
        )

    @staticmethod
    def _build_registry(
        ocr_engine: OCREngine | None, vision_describer: VisionDescriber | None
    ) -> dict[str, Extractor]:
        image_extractor = ImageExtractor(ocr_engine=ocr_engine, vision_describer=vision_describer)
        return {
            ".pdf": PdfExtractor(),
            ".docx": DocxExtractor(),
            ".txt": PlainTextExtractor(file_type="txt"),
            ".md": PlainTextExtractor(file_type="md"),
            ".tex": TexExtractor(),
            ".cls": ClsExtractor(),
            ".bib": BibExtractor(),
            ".java": JavaExtractor(),
            ".png": image_extractor,
            ".jpg": image_extractor,
            ".jpeg": image_extractor,
        }

    @property
    def supported_extensions(self) -> set[str]:
        return set(self._registry) | {".zip"}

    def process(self, file_path: Path | str, document_id: str) -> list[ProcessedChunk]:
        """Returns the chunks for one uploaded file (or ZIP archive).

        Raises DocumentProcessingError if the file is missing, unsupported,
        or contains no extractable content.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise DocumentProcessingError(f"File not found: {file_path}")

        ext = file_path.suffix.lower()
        if ext == ".zip":
            return self._process_zip(file_path, document_id)

        extractor = self._registry.get(ext)
        if extractor is None:
            raise DocumentProcessingError(f"Unsupported extension for extraction: {ext!r}")
        return extractor.extract(file_path, document_id, chunk_index_start=0)

    def _process_zip(self, zip_path: Path, document_id: str) -> list[ProcessedChunk]:
        """Securely unpacks the archive and dispatches each supported
        member to its own extractor, keeping a single continuous
        chunk_index across the whole archive and restoring each member's
        original filename as `source_file`."""
        with tempfile.TemporaryDirectory(prefix="nexus_zip_") as tmp:
            tmp_dir = Path(tmp)
            entries = secure_extract_zip(zip_path, tmp_dir, allowed_extensions=set(self._registry))

            if not entries:
                raise DocumentProcessingError(
                    f"{zip_path.name} contains no supported files "
                    f"({', '.join(sorted(self._registry))})."
                )

            chunks: list[ProcessedChunk] = []
            chunk_index = 0
            for entry in entries:
                ext = "." + entry.relative_path.rsplit(".", 1)[-1].lower()
                extractor = self._registry[ext]
                try:
                    file_chunks = extractor.extract(
                        entry.absolute_path, document_id, chunk_index_start=chunk_index
                    )
                except DocumentProcessingError:
                    # One unreadable/unparseable file inside the archive
                    # must not fail the whole ZIP; skip it and continue.
                    continue

                for chunk in file_chunks:
                    # The extractor only sees the temp extraction path;
                    # restore the original in-archive path (and subfolder,
                    # if any) so callers know exactly where a chunk came
                    # from, instead of "thesis_project.zip".
                    chunk.metadata["source_file"] = entry.relative_path
                    chunk.metadata["source_archive"] = zip_path.name

                chunks.extend(file_chunks)
                chunk_index += len(file_chunks)

            if not chunks:
                raise DocumentProcessingError(
                    f"None of the files inside {zip_path.name} could be processed."
                )
            return chunks


# ---------------------------------------------------------------------------
# Example: how the view/service layer would use this
# ---------------------------------------------------------------------------
#
# from chatbot.models import DocumentChunk
# from chatbot.services.document_processor import DocumentProcessor, DocumentProcessingError
#
# processor = DocumentProcessor()
# try:
#     chunks = processor.process(local_file_path, document_id=str(document.id))
# except DocumentProcessingError as exc:
#     document.status = Document.Status.FAILED
#     document.save(update_fields=["status"])
#     raise
#
# DocumentChunk.objects.bulk_create(
#     [DocumentChunk(**c.to_model_kwargs()) for c in chunks]
# )
# document.status = Document.Status.READY
# document.save(update_fields=["status"])
#
# To plug in real OCR for images (now a ready-made class, not just a
# sketch), with no other change needed anywhere else in this module:
#
# processor = DocumentProcessor(ocr_engine=PytesseractOCR())
#
# (requires: pip install pytesseract, plus the tesseract-ocr system binary)