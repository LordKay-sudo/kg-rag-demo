from unittest.mock import patch

from app.ingest.batch import batch_ingest, iter_document_ids


def test_iter_document_ids_respects_prefix_and_limit(tmp_path):
    (tmp_path / "doc-001.txt").write_text("Title: A\n\nbody", encoding="utf-8")
    (tmp_path / "epmc-1.txt").write_text("Title: B\n\nbody", encoding="utf-8")
    (tmp_path / "epmc-2.txt").write_text("Title: C\n\nbody", encoding="utf-8")

    with patch("app.ingest.batch.settings") as mock_settings:
        mock_settings.documents_dir = tmp_path
        ids = iter_document_ids(prefix="epmc-", limit=1)
    assert ids == ["epmc-1"]


def test_batch_ingest_dry_run(tmp_path):
    (tmp_path / "epmc-1.txt").write_text("Title: T\n\nbody", encoding="utf-8")
    with patch("app.ingest.batch.settings") as mock_settings:
        mock_settings.documents_dir = tmp_path
        results = batch_ingest(prefix="epmc-", dry_run=True)
    assert len(results) == 1
    assert results[0]["status"] == "dry_run"
