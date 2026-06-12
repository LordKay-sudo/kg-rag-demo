from app.ingest.metadata import parse_document


def test_parses_title_and_body_only():
    raw = "Title: BRCA1 and breast cancer risk\n\nBRCA1 mutations increase risk."
    meta = parse_document(raw)
    assert meta.title == "BRCA1 and breast cancer risk"
    assert meta.body == "BRCA1 mutations increase risk."
    assert meta.source is None


def test_parses_full_metadata_header():
    raw = (
        "Title: BRCA1 review\n"
        "Source: Europe PMC\n"
        "PMID: 20301425\n"
        "DOI: 10.1000/example\n"
        "URL: https://example.org/a\n"
        "\n"
        "Body text here."
    )
    meta = parse_document(raw)
    assert meta.title == "BRCA1 review"
    assert meta.source == "Europe PMC"
    assert meta.pmid == "20301425"
    assert meta.doi == "10.1000/example"
    assert meta.url == "https://example.org/a"
    assert meta.body == "Body text here."


def test_fallback_title_when_missing():
    meta = parse_document("Just a body with no header.", fallback_title="doc-001")
    assert meta.title == "doc-001"
    assert "Just a body" in meta.body
