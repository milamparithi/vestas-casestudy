"""Structured output models for risk extraction."""

from __future__ import annotations

from pydantic import BaseModel


class ExtractedRisk(BaseModel):
    """A single risk as returned by the LLM for one page."""

    title: str
    description: str
    category: str
    mitigation: str | None = None


class PageExtraction(BaseModel):
    """The LLM response for a single page."""

    risks: list[ExtractedRisk] = []


class Risk(BaseModel):
    """A risk with provenance attached by the pipeline (not the model)."""

    title: str
    description: str
    category: str
    mitigation: str | None
    section: str
    page: int
