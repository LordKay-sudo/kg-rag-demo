"""Ingest all seed documents (run after seed_documents.py)."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.ingest.pipeline import ingest_all_pending  # noqa: E402


def main() -> None:
    results = ingest_all_pending()
    for r in results:
        print(f"Ingested {r['document_id']}: {r['chunks']} chunks")


if __name__ == "__main__":
    main()
