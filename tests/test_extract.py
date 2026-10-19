import json

import pytest

from risk_pipeline.pipeline import extract as extract_module
from risk_pipeline.pipeline.ingest import Page
from risk_pipeline.pipeline.retrieve import FetchedSection
from risk_pipeline.pipeline.schemas import PageExtraction
from risk_pipeline.utils import llm
from risk_pipeline.utils.config import Settings

SETTINGS = Settings(model="test/model", api_key=None, base_url=None)


def _section(name, pages):
    return FetchedSection(
        name=name,
        page_start=pages[0].page_number,
        page_end=pages[-1].page_number,
        text="",
        pages=pages,
    )


def test_page_extraction_keeps_free_form_category():
    payload = {
        "risks": [
            {
                "title": "Cyber attacks",
                "description": "Threat actors may disrupt operations.",
                "category": "Cyber & data privacy",
                "mitigation": "Zero-trust program",
            }
        ]
    }
    parsed = PageExtraction.model_validate(payload)
    assert parsed.risks[0].category == "Cyber & data privacy"


def test_missing_mitigation_defaults_to_none():
    parsed = PageExtraction.model_validate(
        {"risks": [{"title": "t", "description": "d", "category": "c"}]}
    )
    assert parsed.risks[0].mitigation is None


def test_empty_page_returns_no_risks():
    assert PageExtraction.model_validate({"risks": []}).risks == []


def test_extract_page_parses_client_output(monkeypatch):
    monkeypatch.setattr(
        extract_module,
        "complete_json",
        lambda messages, settings: {
            "risks": [
                {"title": "t", "description": "d", "category": "financial",
                 "mitigation": "m"}
            ]
        },
    )
    risks = extract_module.extract_page("some text", SETTINGS)
    assert risks[0].title == "t"


def test_extract_tags_section_and_page(monkeypatch):
    monkeypatch.setattr(
        extract_module,
        "complete_json",
        lambda messages, settings: {
            "risks": [
                {"title": "t", "description": "d", "category": "  market  ",
                 "mitigation": None}
            ]
        },
    )
    pages = [Page(pdf_index=49, page_number=50, text="a"),
             Page(pdf_index=50, page_number=51, text="b")]
    risks = extract_module.extract([_section("Risk management", pages)], SETTINGS)

    assert len(risks) == 2
    assert [r.page for r in risks] == [50, 51]
    assert all(r.section == "Risk management" for r in risks)
    assert risks[0].category == "market"  # trimmed


def test_extract_skips_failing_page(monkeypatch):
    calls = {"n": 0}

    def flaky(messages, settings):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("boom")
        return {"risks": [{"title": "t", "description": "d", "category": "c"}]}

    monkeypatch.setattr(extract_module, "complete_json", flaky)
    pages = [Page(pdf_index=49, page_number=50, text="a"),
             Page(pdf_index=50, page_number=51, text="b")]
    risks = extract_module.extract([_section("S", pages)], SETTINGS)
    assert len(risks) == 1


class _Msg:
    def __init__(self, content):
        self.content = content


class _Choice:
    def __init__(self, content):
        self.message = _Msg(content)


class _Response:
    def __init__(self, content):
        self.choices = [_Choice(content)]


def test_complete_json_strips_code_fences(monkeypatch):
    monkeypatch.setattr(
        llm.litellm, "completion",
        lambda **kwargs: _Response('```json\n{"risks": []}\n```'),
    )
    assert llm.complete_json([], SETTINGS) == {"risks": []}


def test_complete_json_retries_then_succeeds(monkeypatch):
    responses = iter([_Response("not json"), _Response('{"risks": []}')])
    monkeypatch.setattr(llm.litellm, "completion", lambda **kwargs: next(responses))
    assert llm.complete_json([], SETTINGS) == {"risks": []}


def test_complete_json_raises_after_retries(monkeypatch):
    monkeypatch.setattr(llm.litellm, "completion", lambda **kwargs: _Response("nope"))
    with pytest.raises(ValueError):
        llm.complete_json([], SETTINGS)
