from risk_pipeline.pipeline.retrieve import SECTION_DETAILS, SectionDetail, retrieve_sections

EXPECTED = {
    "Risk management": (50, 51),
    "Material impacts, risks, and opportunities": (71, 74),
    "Climate change": (85, 92),
    "Cyber security": (118, 118),
}


def test_page_numbers_from_labels_or_fallback(pages):
    by_index = {p.pdf_index: p for p in pages}
    assert by_index[49].page_number == 50
    assert by_index[50].page_number == 51
    assert by_index[70].page_number == 71
    assert by_index[117].page_number == 118


def test_all_requested_sections_fetched(pages):
    sections = {s.name: s for s in retrieve_sections(pages)}
    assert set(sections) == set(EXPECTED)
    for name, (start, end) in EXPECTED.items():
        assert (sections[name].page_start, sections[name].page_end) == (start, end)


def test_section_text_is_page_marked(pages):
    sections = {s.name: s for s in retrieve_sections(pages)}
    risk = sections["Risk management"].text
    assert "[p.50]" in risk and "[p.51]" in risk
    assert "Enterprise Risk Management" in risk
    assert "threat actor" in sections["Cyber security"].text.lower()


def test_custom_section_details_are_honored(pages):
    request = [SectionDetail(name="Custom", start_page=118, end_page=118)]
    sections = retrieve_sections(pages, request)
    assert len(sections) == 1
    assert sections[0].name == "Custom"
    assert (sections[0].page_start, sections[0].page_end) == (118, 118)


def test_default_details_cover_assignment_scope(pages):
    assert [d.start_page for d in SECTION_DETAILS] == [50, 71, 85, 118]


def test_sections_expose_pages_but_exclude_them_from_dump(pages):
    section = retrieve_sections(pages)[0]
    assert [p.page_number for p in section.pages] == [50, 51]
    assert "pages" not in section.model_dump()
