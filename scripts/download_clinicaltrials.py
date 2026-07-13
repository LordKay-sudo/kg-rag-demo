#!/usr/bin/env python3
"""Download ClinicalTrials.gov summaries into data/documents for GapForge RAG."""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.ingest.clinicaltrials import download_studies, write_manifest  # noqa: E402

DEFAULT_NCTS = [
    "NCT00105547",  # Flurizan / tarenflurbil AD Phase 3
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Fetch ClinicalTrials.gov studies as corpus docs")
    parser.add_argument("--nct", action="append", dest="ncts", help="NCT id (repeatable)")
    parser.add_argument(
        "--out",
        type=Path,
        default=ROOT / "data" / "documents",
        help="Output directory for .txt documents",
    )
    args = parser.parse_args()
    ncts = args.ncts or DEFAULT_NCTS
    paths = download_studies(ncts, args.out)
    manifest = ROOT / "data" / "documents" / "manifest" / "ctgov_manifest.json"
    write_manifest(
        paths,
        manifest,
        note="ClinicalTrials.gov API v2 summaries for GapForge dual-channel evidence",
    )
    for p in paths:
        print(f"Wrote {p}")
    print(f"Manifest: {manifest}")


if __name__ == "__main__":
    main()
