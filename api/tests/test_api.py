from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    with patch("app.routers.health.check_connectivity", return_value=True):
        r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["neo4j"] is True


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
