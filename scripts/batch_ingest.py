"""Batch-ingest corpus files with progress (roadmap R14).

Usage:
    py -3 scripts/batch_ingest.py
    py -3 scripts/batch_ingest.py --prefix epmc- --limit 3
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.ingest.batch import batch_ingest  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Batch ingest documents into Neo4j")
    parser.add_argument("--prefix", default="", help="Only ingest ids starting with this prefix")
    parser.add_argument("--limit", type=int, default=None, help="Max documents to ingest")
    parser.add_argument("--dry-run", action="store_true", help="List documents without ingesting")
    args = parser.parse_args()

    batch_ingest(prefix=args.prefix, limit=args.limit, dry_run=args.dry_run)


if __name__ == "__main__":
    main()
