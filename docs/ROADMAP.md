# kg-rag-demo — implementation roadmap

**Repo:** [kg-rag-demo](https://github.com/LordKay-sudo/kg-rag-demo) (citation-grounded document RAG)  
**Pairs with:** [bioinsight-graph](https://github.com/LordKay-sudo/bioinsight-graph) (structured associations)  
**Consumed by:** [embabel-mcp](https://github.com/LordKay-sudo/embabel-mcp) when `KG_RAG_ENABLED=true`  
**Compact context:** [ECOSYSTEM_CONTEXT.md](https://github.com/LordKay-sudo/bioinsight-graph/blob/main/docs/ECOSYSTEM_CONTEXT.md)

Optional third repo — enable only when demonstrating **structured + unstructured** evidence.

---

## Positioning

**Unstructured** biomedical text → chunks → entities → vectors → **cited** answers. Complements BioInsight’s **curated graph**, not replaces it.

Refinements from ontology/GraphRAG literature ([UniAI-GraphRAG](https://arxiv.org/html/2603.25152v3), [ML6 biomedical KG](https://blog.ml6.eu/accelerating-biomedical-knowledge-graph-construction-with-llms-db429952f4b2), [production ontology GraphRAG](https://medium.com/@aiwithakashgoyal/beyond-simple-extraction-how-production-grade-ontologies-transform-graphrag-from-prototype-to-333742fa41a6)):

- **Ontology-guided extraction** — constrain LLM/rule extract to allowed types (Gene, Disease, Drug, `ASSOCIATED_WITH`, etc.)
- **Normalize after extract** — merge synonyms/duplicates before Neo4j write (ML6 uniformisation agent pattern)
- **Plan-aware + dual-channel** with BioInsight — graph dossier first, literature second (see embabel **M8**)

---

## Shipped (baseline)

| Item |
|------|
| 10-doc seed corpus, ingest pipeline, Neo4j Document/Chunk schema |
| Rule-based Gene/Disease/Drug extraction |
| MiniLM embeddings, `POST /ask`, React Ask/Corpus/Graph |
| Docker Compose, CI |
| MCP bridge via embabel-mcp (optional) |

---

## P0 — Trust chain (do first)

| ID | Task | Done when |
|----|------|-----------|
| ✓ **R1** | Every `POST /ask` answer includes **citation block**: chunk id, doc title, passage excerpt | Citations carry `document_title` + snippet |
| ✓ **R2** | Resolve **PMID / DOI / Europe PMC URL** when present in source metadata | `reference_url` via `app/references.py` |
| ✓ **R3** | `GET /documents/{id}/chunks` or equivalent for audit trail | Returns chunks + entities + reference_url |
| ✓ **R4** | README + API: explicit **demo corpus, not clinical** disclaimer | `disclaimer` on `/health`; README + PROVENANCE.md |

---

## P1 — One platform story (with BioInsight)

| ID | Task | Depends on | Done when |
|----|------|------------|-----------|
| ✓ **R5** | Entity resolution: extracted genes → **ENSG**, diseases → **EFO/MONDO** (lookup table or API) | BioInsight 2.x | `app/identifiers.py`; `ontology_id` on Gene/Disease nodes |
| ✓ **R6** | **`POST /ask` optional `gene_id` / `disease_id`** — bias retrieval toward graph-aligned entities | R5 | Params in OpenAPI; biased chunk boost |
| ✓ **R7** | Extraction **provenance**: chunk id, extractor version, confidence on entities | — | On `MENTIONS` edges; in `/documents/{id}/chunks` |
| ✓ **R8** | Notebook: BRCA1 — BioInsight scores + kg-rag quotes side by side | BioInsight 4.4 | [notebooks/brca1_structured_vs_literature.ipynb](../notebooks/brca1_structured_vs_literature.ipynb) |
| **R16** | `docs/EXTRACTION_SCHEMA.md` — schema **S=(E,R,Φ)**: allowed entities, relations, domain/range rules | — | Extractor/prompt references schema |
| **R17** | **Normalization pipeline** after extract: dedupe symbols, map aliases before graph write | R16 | Documented step in ingest README |

---

## P2 — Plan-aware RAG (PRoH-style process)

| ID | Task | Done when |
|----|------|-----------|
| **R9** | **`POST /ask/plan`** (or prompt contract): decompose question → sub-queries + which entities | Returns plan JSON before retrieval |
| **R10** | **Conditional retrieval**: if graph API reports weak evidence (optional header/param), widen lexical/vector query | Documented in README |
| **R11** | Synonym / symbol merge for gene names (BRCA1, BRCA-1) in extractor or query expander | Fewer missed hits |
| **R12** | Token-efficient mode: top-k chunks cap with “insufficient evidence” flag | Honest partial answers |

---

## P3 — Corpus scale (optional)

| ID | Task | Done when |
|----|------|-----------|
| **R13** | Ingest 50–100 open-access abstracts (Europe PMC) with licence file | `PROVENANCE.md` in repo |
| **R14** | Batch ingest CLI + progress | CI smoke on 3 docs |
| **R15** | Compare retrieval metrics on fixed question set (3–5 questions) | `docs/BENCHMARKS.md` |

---

## MCP / embabel coordination

| embabel task | kg-rag task |
|--------------|-------------|
| M8 conditional graph-and-literature | R1–R2 citations |
| M4 evidence from graph | R6 entity-biased ask |
| M7 provenance bundle | R3 chunk audit |

---

## Explicit non-goals

- Replacing BioInsight structured ingest
- Clinical decision support
- Full PRoH / UniAI-GraphRAG codebase import
- Microsoft GraphRAG **community report** pipeline on 10-doc demo corpus
- LangChain as required core dependency
- PubMed-scale LLM KG (MedKGent-scale) without confidence filtering and licences

## References (optional reading)

- [Towards AI — Neo4j + LangChain GraphRAG](https://pub.towardsai.net/graphrag-explained-building-knowledge-grounded-llm-systems-with-neo4j-and-langchain-017a1820763e)  
- [Neo4j field — PubMed KG generation](https://github.com/neo4j-field/pubmed-knowledge-graph-generation) — extract + resolve + Cypher agent patterns  
- [DeepSense — ontology-driven GraphRAG](https://deepsense.ai/resource/ontology-driven-knowledge-graph-for-graphrag/)

---

## Task pick order

1. **R1 → R4** (citations + trust)  
2. **R16 → R17** (schema + normalization — before scaling corpus)  
3. **R5 → R6** (IDs — after BioInsight 2.x)  
4. **R8** (demo notebook)  
5. **R9 → R11** (plan-aware)  
6. **R13+** if time

---

*Living doc — PRs reference task IDs (e.g. `R2`).*
