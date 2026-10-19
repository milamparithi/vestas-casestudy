from risk_pipeline.pipeline.ingest import Page


def test_ingest_indexes_all_pages(pages):
    assert len(pages) == 195
    assert [p.pdf_index for p in pages] == list(range(195))


def test_page_number_matches_printed_page(pages):
    by_index = {p.pdf_index: p for p in pages}
    assert "Main risks" in by_index[50].text  # printed page 51
    assert by_index[50].page_number == 51


def test_target_sections_present(pages):
    text = {p.pdf_index: p.text for p in pages}
    assert "Enterprise Risk Management" in text[49]
    assert "Main risks" in text[50]
    assert "Material impacts, risks" in text[70]
    assert "Climate Change" in text[84]
    assert "Cyber security" in text[117]


def test_no_empty_pages(pages):
    for page in pages:
        assert len(page.text.strip()) > 0, f"empty page {page.pdf_index}"
        assert isinstance(page, Page)
