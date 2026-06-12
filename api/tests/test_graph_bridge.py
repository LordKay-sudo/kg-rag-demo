from unittest.mock import MagicMock, patch

from app.rag.graph_bridge import graph_evidence_is_weak


@patch("app.rag.graph_bridge.settings")
def test_weak_when_no_diseases(mock_settings):
    mock_settings.bioinsight_api_url = "http://localhost:8000"
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"diseases": []}
    mock_response.raise_for_status = MagicMock()

    with patch("httpx.Client") as client_cls:
        client_cls.return_value.__enter__.return_value.get.return_value = mock_response
        assert graph_evidence_is_weak("BRCA1") is True


@patch("app.rag.graph_bridge.settings")
def test_not_weak_when_bioinsight_unconfigured(mock_settings):
    mock_settings.bioinsight_api_url = ""
    assert graph_evidence_is_weak("BRCA1") is False
