"""Download open-access Europe PMC abstracts into data/documents/ (roadmap R13).

Usage:
    py -3 scripts/download_europepmc.py --max-total 60
    py -3 scripts/download_europepmc.py --genes BRCA1,TP53 --max-per-gene 5
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.ingest.europepmc import DEFAULT_GENES, download_corpus  # noqa: E402


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Europe PMC OA abstracts")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=ROOT / "data" / "documents",
        help="Directory for epmc-<pmid>.txt files",
    )
    parser.add_argument(
        "--manifest",
        type=Path,
        default=ROOT / "data" / "documents" / "manifest" / "epmc_manifest.json",
    )
    parser.add_argument("--genes", default="", help="Comma-separated gene symbols")
    parser.add_argument("--max-per-gene", type=int, default=6)
    parser.add_argument("--max-total", type=int, default=60)
    args = parser.parse_args()

    genes = [g.strip() for g in args.genes.split(",") if g.strip()] or DEFAULT_GENES
    manifest = download_corpus(
        genes=genes,
        max_per_gene=args.max_per_gene,
        max_total=args.max_total,
        output_dir=args.output_dir,
        manifest_path=args.manifest,
    )
    print(f"Downloaded {manifest['document_count']} documents -> {args.output_dir}")
    print(f"Manifest: {args.manifest}")


if __name__ == "__main__":
    main()
