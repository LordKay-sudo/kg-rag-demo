from app.references import normalize_doi, normalize_pmid, resolve_reference_url


def test_url_wins_over_everything():
    url = resolve_reference_url(
        url="https://example.org/article",
        doi="10.1000/xyz",
        pmid="20301425",
        title="BRCA1 review",
    )
    assert url == "https://example.org/article"


def test_doi_preferred_over_pmid():
    url = resolve_reference_url(doi="10.1000/xyz", pmid="20301425", title="BRCA1")
    assert url == "https://doi.org/10.1000/xyz"


def test_pmid_resolves_to_europe_pmc_article():
    url = resolve_reference_url(pmid="20301425", title="BRCA1")
    assert url == "https://europepmc.org/article/MED/20301425"


def test_title_fallback_is_europe_pmc_search():
    url = resolve_reference_url(title="BRCA1 and breast cancer risk")
    assert url is not None
    assert url.startswith("https://europepmc.org/search?query=")
    assert "BRCA1" in url


def test_no_metadata_returns_none():
    assert resolve_reference_url() is None


def test_normalize_pmid_strips_prefix():
    assert normalize_pmid("PMID: 12345") == "12345"
    assert normalize_pmid("not-a-pmid") is None


def test_normalize_doi_strips_url_and_prefix():
    assert normalize_doi("https://doi.org/10.1000/abc") == "10.1000/abc"
    assert normalize_doi("doi:10.1000/abc") == "10.1000/abc"
    assert normalize_doi("nonsense") is None
