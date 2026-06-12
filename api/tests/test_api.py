from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    with patch("app.routers.health.check_connectivity", return_value=True):
        r = client.get("/api/v1/health")
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "ok"
    assert body["neo4j"] is True
    assert "not clinical-grade" in body["disclaimer"]


def test_document_chunks_audit_trail():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(
            single=lambda: {
                "id": "doc-001",
                "title": "BRCA1 and breast cancer risk",
                "source": "Synthetic demo abstract",
                "pmid": "20301425",
                "doi": None,
                "url": None,
            }
        ),
        MagicMock(
            data=lambda: [
                {
                    "chunk_id": "doc-001-chunk-0",
                    "index": 0,
                    "text": "BRCA1 increases breast cancer risk.",
                    "entities": [
                        {
                            "type": "Gene",
                            "id": "BRCA1",
                            "ontology_id": "ENSG00000012048",
                            "confidence": 0.9,
                            "extractor_version": "rule-v1",
                        }
                    ],
                }
            ]
        ),
    ]
    with patch("app.routers.documents.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/documents/doc-001/chunks")
    assert r.status_code == 200
    body = r.json()
    assert body["document_id"] == "doc-001"
    assert body["chunk_count"] == 1
    assert body["reference_url"] == "https://europepmc.org/article/MED/20301425"
    entity = body["chunks"][0]["entities"][0]
    assert entity["ontology_id"] == "ENSG00000012048"
    assert entity["confidence"] == 0.9
    assert entity["extractor_version"] == "rule-v1"


def test_document_chunks_not_found():
    session = MagicMock()
    session.run.return_value.single.return_value = None
    with patch("app.routers.documents.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/documents/missing/chunks")
    assert r.status_code == 404


def test_explore_graph():
    session = MagicMock()
    session.run.side_effect = [
        MagicMock(
            single=lambda: {
                "label": "Gene",
                "id": "BRCA1",
                "name": None,
                "symbol": "BRCA1",
                "title": None,
            }
        ),
        MagicMock(
            data=lambda: [
                {"label": "Gene", "id": "BRCA1", "name": None, "symbol": "BRCA1", "title": None},
                {"label": "Disease", "id": "breast_cancer", "name": "breast cancer", "symbol": None, "title": None},
            ]
        ),
        MagicMock(
            data=lambda: [
                {"source": "BRCA1", "target": "breast_cancer", "type": "ASSOCIATED_WITH"},
            ]
        ),
    ]
    with patch("app.routers.graph.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/graph/explore", params={"entity_id": "BRCA1"})
    assert r.status_code == 200
    body = r.json()
    assert body["entity_id"] == "BRCA1"
    assert len(body["nodes"]) == 2
    assert body["links"][0]["type"] == "ASSOCIATED_WITH"


def test_explore_not_found():
    session = MagicMock()
    session.run.return_value.single.return_value = None
    with patch("app.routers.graph.get_session") as mock_get:
        mock_get.return_value.__enter__.return_value = session
        r = client.get("/api/v1/graph/explore", params={"entity_id": "MISSING"})
    assert r.status_code == 404


def test_ask_plan_endpoint():
    r = client.post(
        "/api/v1/ask/plan",
        json={"question": "What links BRCA1 to breast cancer?"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["intent"] == "gene_disease"
    assert body["suggested_gene_id"] == "BRCA1"
    assert len(body["steps"]) >= 2
