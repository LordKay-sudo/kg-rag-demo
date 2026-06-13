"""Batch document ingest helpers (roadmap R14)."""
from __future__ import annotations

import time
from pathlib import Path

from app.config import settings
from app.ingest.pipeline import ingest_document


def iter_document_ids(*, prefix: str = "", limit: int | None = None) -> list[str]:
    paths = sorted(settings.documents_dir.glob("*.txt"))
    if prefix:
        paths = [p for p in paths if p.stem.startswith(prefix)]
    ids = [p.stem for p in paths]
    return ids[:limit] if limit else ids


def batch_ingest(
    *,
    prefix: str = "",
    limit: int | None = None,
    dry_run: bool = False,
) -> list[dict]:
    doc_ids = iter_document_ids(prefix=prefix, limit=limit)
    total = len(doc_ids)
    results: list[dict] = []
    start = time.perf_counter()

    for idx, doc_id in enumerate(doc_ids, start=1):
        if dry_run:
            print(f"[{idx}/{total}] would ingest {doc_id}")
            results.append({"document_id": doc_id, "status": "dry_run"})
            continue
        try:
            result = ingest_document(doc_id)
            results.append(result)
            print(f"[{idx}/{total}] ingested {doc_id}: {result['chunks']} chunks")
        except Exception as exc:
            print(f"[{idx}/{total}] FAILED {doc_id}: {exc}")
            results.append({"document_id": doc_id, "status": "error", "error": str(exc)})

    elapsed = time.perf_counter() - start
    ok = sum(1 for r in results if r.get("status") == "ingested")
    print(f"Done: {ok}/{total} ingested in {elapsed:.1f}s")
    return results
