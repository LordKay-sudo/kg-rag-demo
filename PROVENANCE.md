# Provenance & data disclaimer

## Demo corpus

The seed corpus in `data/documents/` includes:

1. **10 synthetic biomedical-style abstracts** (`doc-001` … `doc-010`) — written for
   demonstration, marked `Source: Synthetic demo abstract (not a real publication)`.
2. **Europe PMC open-access abstracts** (`epmc-<PMID>.txt`) — optional scale corpus
   downloaded via `scripts/download_europepmc.py` (roadmap R13).

Use this project to demonstrate the *pipeline* (chunk → extract → embed → cited Q&A),
not to look up factual biomedical claims without verifying primary sources.

## Europe PMC open-access ingest (R13)

| Item | Detail |
|------|--------|
| **API** | [Europe PMC REST search](https://europepmc.org/RestfulWebService) |
| **Filter** | `OPEN_ACCESS:Y` and `HAS_ABSTRACT:Y` per gene query |
| **Licence** | Open-access full text only; **per-article licence is set by the publisher** (many are [CC BY](https://creativecommons.org/licenses/by/4.0/)). Verify on the article page before redistribution. |
| **Manifest** | `data/documents/manifest/epmc_manifest.json` — PMIDs, titles, DOIs, gene queries |
| **Download** | `py -3 scripts/download_europepmc.py --max-total 60` |
| **Batch ingest** | `py -3 scripts/batch_ingest.py --prefix epmc-` |

Europe PMC data is provided by the Europe PMC consortium. This demo stores abstract
text locally for embedding/RAG; it does **not** mirror the full Open Targets or PubMed
licence terms — check each record's licence field on Europe PMC.

## Source metadata format

Each document supports an optional header that drives citation links:

| Key | Meaning | Used for |
|-----|---------|----------|
| `Title` | Document title (required) | Citation label, `document_title` |
| `Source` | Free-text provenance | Shown in citation |
| `PMID` | PubMed id | Europe PMC article URL |
| `DOI` | Digital Object Identifier | `https://doi.org/<doi>` |
| `URL` | Canonical source URL | Used verbatim if present |

Citation `reference_url` resolution order: **URL → DOI → PMID → Europe PMC title search**.
The title-search fallback never fabricates a specific article id.

## Shared identifiers (one platform story)

Genes and diseases resolve to the same public ontology ids that
[BioInsight Graph](https://github.com/LordKay-sudo/bioinsight-graph) uses as graph keys:

- Genes → Ensembl **`ENSG`** ids (e.g. `BRCA1` → `ENSG00000012048`)
- Diseases → **EFO / MONDO** ids (e.g. `breast_cancer` → `EFO_0000305`)

The mapping lives in [`api/app/identifiers.py`](api/app/identifiers.py). Ids are real,
stable public identifiers; the *associations between them in the demo corpus* are
illustrative, not curated evidence.

## Non-goals

- Not clinical decision support or diagnosis.
- Not a substitute for BioInsight's curated structured ingest.
- Associations extracted from text are **correlative and illustrative**, not causal.
