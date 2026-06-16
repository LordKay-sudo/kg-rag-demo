# kg-rag extraction schema

Compact schema \(S = (E, R, \Phi)\) for **text-derived** entities in kg-rag-demo.
Matches Neo4j labels, the rule-based extractor, and the post-extract normalizer.

**Structured graph (Open Targets ingest):** see [BioInsight ONTOLOGY_SCHEMA](https://github.com/LordKay-sudo/bioinsight-graph/blob/main/docs/ONTOLOGY_SCHEMA.md).

**Code:** [`api/app/ingest/schema.py`](../api/app/ingest/schema.py) · [`extractor.py`](../api/app/ingest/extractor.py) · [`normalize.py`](../api/app/ingest/normalize.py)

---

## Entity types (E)

| Type | Graph key (`id`) | `ontology_id` (optional) | Extraction rule |
|------|------------------|--------------------------|-----------------|
| **Gene** | HGNC symbol (uppercase) | Ensembl `ENSG` | Token in `GENE_ALLOWLIST` after alias expansion |
| **Disease** | slug (`breast_cancer`) | EFO / MONDO | Phrase match in `DISEASE_PHRASES` |
| **Drug** | lowercase name | — | Name in `DRUG_NAMES` |

Only these three labels may be created by the demo extractor. Unknown tokens are ignored.

---

## Relation types (R)

| Relation | Domain → Range | Properties (Φ) | Confidence default |
|----------|----------------|----------------|-------------------|
| `ASSOCIATED_WITH` | Gene → Disease | `confidence`, `evidence_chunk_id` | 0.7 |
| `TREATS` | Drug → Disease | `confidence`, `evidence_chunk_id` | 0.6 |

Relations are **co-occurrence hypotheses** from the same chunk — not curated clinical claims.

---

## Validation (Φ)

1. **Entity allowlist** — genes must appear in `GENE_ALLOWLIST`; diseases/drugs must match curated phrase/name tables.
2. **Domain / range** — only schema relations with matching endpoint types are written.
3. **Ontology join** — after normalization, `resolve_entity_id()` maps Gene → `ENSG`, Disease → EFO/MONDO ([`identifiers.py`](../api/app/identifiers.py)).
4. **Provenance** — `MENTIONS` edges store `confidence` and `extractor_version` (R7).

---

## Ingest pipeline order

```text
parse document → chunk text → embed chunks
  → extract_entities()     # rule-based, schema-constrained
  → normalize_extraction() # R17: aliases, dedupe, validate relations
  → MERGE Neo4j nodes/edges
```

| Step | Module | Output |
|------|--------|--------|
| Extract | `app/ingest/extractor.py` | Raw `ExtractedEntity` / `ExtractedRelation` lists per chunk |
| Normalize | `app/ingest/normalize.py` | Canonical ids, deduped entities, schema-valid relations |
| Resolve | `app/identifiers.py` | `ontology_id` on Gene/Disease nodes |
| Write | `app/ingest/pipeline.py` | Neo4j `Document`, `Chunk`, `MENTIONS`, typed relations |

---

## Gene alias normalization

Hyphenated and legacy forms map to canonical symbols before dedupe (shared with query expansion, R11):

| Alias | Canonical |
|-------|-----------|
| BRCA-1 | BRCA1 |
| BRCA-2 | BRCA2 |
| TP-53, P53 | TP53 |

Defined in [`app/rag/query_expand.py`](../api/app/rag/query_expand.py); applied in both extraction and `/ask` query expansion.

---

## Non-goals

- Schema-free LLM triple extraction at ingest scale
- New relation types without updating `RELATION_TYPES` and tests
- Replacing BioInsight curated `ASSOCIATED_WITH` evidence from Open Targets

---

*Living doc — PRs reference task IDs (e.g. `R16`). Bump `EXTRACTOR_VERSION` when allowlists or rules change.*
