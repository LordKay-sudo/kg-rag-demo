import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from app.ingest.europepmc import (
    format_epmc_document,
    search_open_access_abstracts,
)
from app.ingest.metadata import parse_document

FIXTURE = Path(__file__).resolve().parent / "fixtures" / "europepmc_search_brca1.json"


def test_format_epmc_document_includes_pmid_and_url():
    raw = format_epmc_document(
        title="BRCA1 review",
        abstract="BRCA1 is a tumor suppressor.",
        pmid="12345678",
        doi="10.1000/example.1",
    )
    meta = parse_document(raw)
    assert meta.title == "BRCA1 review"
    assert meta.pmid == "12345678"
    assert meta.doi == "10.1000/example.1"
    assert "BRCA1 is a tumor suppressor" in meta.body
    assert "europepmc.org/article/MED/12345678" in meta.url


def test_search_open_access_abstracts_parses_fixture():
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    mock_response = MagicMock()
    mock_response.raise_for_status = MagicMock()
    mock_response.json.return_value = payload
    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    hits, next_cursor = search_open_access_abstracts("BRCA1", client=mock_client)
    assert len(hits) == 1
    assert hits[0]["pmid"] == "12345678"
    assert next_cursor == "cursor-2"
