# GapForge data plane notes

Companion hardening for literature + trials used by dual-channel GapForge evidence.

## ClinicalTrials.gov

```bash
cd kg-rag-demo
py -3 scripts/download_clinicaltrials.py --nct NCT00105547
# then seed + ingest documents as usual
py -3 scripts/seed_documents.py
py -3 scripts/ingest_all.py
```

Offline stub already present: `data/documents/ctgov-nct00105547.txt` and `data/documents/doc-gapforge-flurizan.txt`.

Module: `api/app/ingest/clinicaltrials.py`

## Europe PMC

Existing pipeline unchanged:

```bash
py -3 scripts/download_europepmc.py
```

Prefer OA abstracts with PMIDs for citation URLs in `/ask`.

## PeerLens pre-filter

Before trusting a DOI/arXiv paper into a production corpus, call:

```python
from app.ingest.peerlens_filter import filter_paper

result = filter_paper("10.1038/nature12373")  # requires PeerLens on PEERLENS_API_URL
if not result.allowed:
    raise SystemExit(result.reasons)
```

- Blocks `severity=concern` and `paper_retracted` by default
- `fail_open=True` if PeerLens is down (demo-friendly); set `fail_open=False` in stricter deployments

Env: `PEERLENS_API_URL` (default `http://localhost:8000`)

## Open Targets scale-up (bioinsight-graph)

Use bulk FTP path (already documented in PROVENANCE.md):

```bash
py -3 scripts/download_opentargets_bulk.py --release 24.06 --max-genes 2000
py -3 scripts/etl_opentargets.py --input data/raw/opentargets_bulk.json --strict
py -3 scripts/seed_neo4j.py --strict
```

Keep frozen CI fixtures for reproducible tests.
