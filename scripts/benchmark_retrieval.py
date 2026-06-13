"""Retrieval benchmark on a fixed question set (roadmap R15).

Requires Neo4j seeded + ingested corpus. Reports top-1 chunk score per question.

Usage:
    py -3 scripts/benchmark_retrieval.py
"""
from __future__ import annotations

import argparse
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.rag.orchestrator import ask  # noqa: E402
from app.rag.query_expand import expand_question  # noqa: E402
from app.rag.retriever import retrieve_chunks  # noqa: E402

# Fixed evaluation set (3–5 questions) — reproducible across hosts.
QUESTIONS = [
    ("What is the link between BRCA1 and breast cancer?", "BRCA1", None),
    ("Which drugs are mentioned for melanoma?", None, None),
    ("How does CFTR relate to cystic fibrosis?", "CFTR", None),
    ("What role does TP53 play in lung carcinoma?", "TP53", None),
    ("Tell me about PTEN in prostate cancer.", "PTEN", None),
]


def main() -> None:
    parser = argparse.ArgumentParser(description="Benchmark kg-rag retrieval")
    parser.add_argument(
        "--full-ask",
        action="store_true",
        help="Also run full /ask (slower; requires LLM or fallback path)",
    )
    args = parser.parse_args()

    print(f"{'question':<52}{'top_score':>10}{'citations':>10}{'ms':>8}")
    scores: list[float] = []
    for question, gene_id, disease_id in QUESTIONS:
        start = time.perf_counter()
        expanded = expand_question(question)
        chunks = retrieve_chunks(expanded)
        top = chunks[0].score if chunks else 0.0
        scores.append(top)

        cites = 0
        if args.full_ask:
            result = ask(question, gene_id=gene_id, disease_id=disease_id, compact=True)
            cites = len(result.get("citations") or [])

        ms = (time.perf_counter() - start) * 1000.0
        label = question[:50] + ("…" if len(question) > 50 else "")
        print(f"{label:<52}{top:10.3f}{cites:10d}{ms:8.0f}")

    if scores:
        print(
            f"\nTop-1 score mean={statistics.mean(scores):.3f} "
            f"p50={statistics.median(scores):.3f} n={len(scores)}"
        )
    print("\nRecord these numbers in docs/BENCHMARKS.md after a local ingest.")


if __name__ == "__main__":
    main()
