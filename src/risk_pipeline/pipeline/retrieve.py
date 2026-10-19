"""Fetch report sections by page range and return their text.

The pipeline is told which sections to fetch (name + printed page range) and
makes no assumptions about document structure, table layout, or numbering
beyond what the PDF itself provides.
"""

from __future__ import annotations

import logging

from pydantic import BaseModel, Field

from risk_pipeline.pipeline.ingest import Page

logger = logging.getLogger(__name__)


class SectionDetail(BaseModel):
    """A section to fetch, identified by name and printed page range."""

    name: str
    start_page: int
    end_page: int


class FetchedSection(BaseModel):
    """A fetched section with its page-marked text and underlying pages."""

    name: str
    page_start: int
    page_end: int
    text: str
    pages: list[Page] = Field(exclude=True)


SECTION_DETAILS: list[SectionDetail] = [
    SectionDetail(name="Risk management", start_page=50, end_page=51),
    SectionDetail(
        name="Material impacts, risks, and opportunities", start_page=71, end_page=74
    ),
    SectionDetail(name="Climate change", start_page=85, end_page=92),
    SectionDetail(name="Cyber security", start_page=118, end_page=118),
]


def _select_pages(
    detail: SectionDetail, pages: list[Page], by_page_number: dict[int, Page]
) -> list[Page]:
    """Select the pages for a section.

    Prefer the printed page numbers reported by the PDF (page labels); if none
    are found, fall back to treating the printed number as ``pdf_index + 1``.
    """
    matched = [
        by_page_number[n]
        for n in range(detail.start_page, detail.end_page + 1)
        if n in by_page_number
    ]
    if matched:
        return matched

    by_index = {p.pdf_index: p for p in pages}
    return [
        by_index[i]
        for i in range(detail.start_page - 1, detail.end_page)
        if i in by_index
    ]


def retrieve_sections(
    pages: list[Page], section_details: list[SectionDetail] = SECTION_DETAILS
) -> list[FetchedSection]:
    """Fetch the requested sections as page-marked text."""
    by_page_number = {p.page_number: p for p in pages}

    sections = []
    for detail in section_details:
        selected = _select_pages(detail, pages, by_page_number)
        if not selected:
            logger.warning(
                "No pages found for section %r (pages %d-%d)",
                detail.name,
                detail.start_page,
                detail.end_page,
            )
            continue
        text = "\n\n".join(f"[p.{p.page_number}]\n{p.text}" for p in selected)
        sections.append(
            FetchedSection(
                name=detail.name,
                page_start=selected[0].page_number,
                page_end=selected[-1].page_number,
                text=text,
                pages=selected,
            )
        )
    logger.info("Fetched %d sections", len(sections))
    return sections
