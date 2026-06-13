# Benchmarks (roadmap R15)

Retrieval quality on the **fixed question set** in `scripts/benchmark_retrieval.py`.
Numbers are environment-dependent — reproduce after ingesting the corpus.

## Corpus size

| Corpus | Documents | How |
|--------|-----------|-----|
| Synthetic seed | 10 | `data/documents/doc-*.txt` (shipped) |
| Europe PMC OA | up to 60 | `py -3 scripts/download_europepmc.py --max-total 60` |

After download + ingest, check document count:

```bash
curl http://localhost:8001/api/v1/documents
```

## Retrieval benchmark

Requires Neo4j running and corpus ingested (`scripts/batch_ingest.py`).

```bash
py -3 scripts/benchmark_retrieval.py
py -3 scripts/benchmark_retrieval.py --full-ask   # includes /ask citation counts
```

The harness prints **top-1 vector similarity score** per question (higher = better match).

| Question (truncated) | top-1 score | notes |
|---------------------|------------:|-------|
| BRCA1 ↔ breast cancer | — | run locally |
| drugs for melanoma | — | |
| CFTR ↔ cystic fibrosis | — | |
| TP53 in lung carcinoma | — | |
| PTEN in prostate cancer | — | |

> Fill in after `batch_ingest` on a host with sentence-transformers embeddings loaded.

## Ingest throughput

```bash
Measure-Command { py -3 scripts/batch_ingest.py --prefix epmc- --limit 10 }
```

Record wall time and chunks/sec on your machine in this table when scaling the corpus.
