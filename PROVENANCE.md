# Provenance & data disclaimer

## Demo corpus

The seed corpus in `data/documents/` is **10 synthetic biomedical-style abstracts**
written for demonstration. They are **not real publications** — each file is marked
`Source: Synthetic demo abstract (not a real publication)`.

Use this project to demonstrate the *pipeline* (chunk → extract → embed → cited Q&A),
not to look up factual biomedical claims.

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
