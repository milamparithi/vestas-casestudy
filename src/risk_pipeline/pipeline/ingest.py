"""PDF ingestion: load a report and index its pages.

Text is extracted with pypdf (fast, good for prose). If a page yields
suspiciously little text, it is re-extracted with pdfplumber (layout-aware,
recovers text pypdf misses).
"""

from __future__ import annotations

import logging
from pathlib import Path

import pdfplumber
import pypdf
from pydantic import BaseModel

logger = logging.getLogger(__name__)

SPARSE_PAGE_THRESHOLD = 100  # chars; below this we retry with pdfplumber


class Page(BaseModel):
    """One page of the report with its positional metadata."""

    pdf_index: int  # 0-based position in the file
    page_number: int  # printed page number (from PDF page labels, else pdf_index + 1)
    text: str


def _page_number(label: str | None, index: int) -> int:
    """Use the PDF's standard page label when numeric, else fall back to index."""
    if label and label.strip().isdigit():
        return int(label)
    return index + 1


def _extract_with_pypdf(path: Path) -> list[Page]:
    reader = pypdf.PdfReader(path)
    # Standard /PageLabels-based numbering; pypdf returns index-based strings
    # when the document has no page labels.
    labels = reader.page_labels
    pages = []
    for index, pdf_page in enumerate(reader.pages):
        text = pdf_page.extract_text() or ""
        label = labels[index] if index < len(labels) else None
        pages.append(
            Page(pdf_index=index, page_number=_page_number(label, index), text=text)
        )
    return pages


def _refine_sparse_pages(path: Path, pages: list[Page]) -> int:
    """Re-extract sparse pages with pdfplumber. Returns number refined."""
    sparse = [p for p in pages if len(p.text.strip()) < SPARSE_PAGE_THRESHOLD]
    if not sparse:
        return 0

    refined = 0
    with pdfplumber.open(path) as pdf:
        for page in sparse:
            text = pdf.pages[page.pdf_index].extract_text() or ""
            if len(text) > len(page.text):
                page.text = text
                refined += 1
    return refined


def ingest(path: str | Path) -> list[Page]:
    """Load a PDF report into a list of indexed pages."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"Report not found: {path}")

    pages = _extract_with_pypdf(path)
    refined = _refine_sparse_pages(path, pages)
    empty = sum(1 for p in pages if not p.text.strip())

    logger.info(
        "Ingested %s: %d pages, %d refined via pdfplumber, %d empty",
        path.name,
        len(pages),
        refined,
        empty,
    )
    return pages
