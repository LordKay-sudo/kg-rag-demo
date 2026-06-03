# kg-rag-demo — implementation roadmap

**Repo:** [kg-rag-demo](https://github.com/LordKay-sudo/kg-rag-demo) (citation-grounded document RAG)  
**Pairs with:** [bioinsight-graph](https://github.com/LordKay-sudo/bioinsight-graph) (structured associations)  
**Consumed by:** [embabel-mcp](https://github.com/LordKay-sudo/embabel-mcp) when `KG_RAG_ENABLED=true`  
**Compact context:** [ECOSYSTEM_CONTEXT.md](https://github.com/LordKay-sudo/bioinsight-graph/blob/main/docs/ECOSYSTEM_CONTEXT.md)

Optional third repo — enable only when demonstrating **structured + unstructured** evidence.

---

## Positioning

**Unstructured** biomedical text → chunks → entities → vectors → **cited** answers. Complements BioInsight’s **curated graph**, not replaces it. PRoH-inspired refinement here = **plan-aware retrieval** (use graph gaps to steer queries) and **shared identifiers** — not building a knowledge hypergraph engine.

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
| **R1** | Every `POST /ask` answer includes **citation block**: chunk id, doc title, passage excerpt | No orphan claims |
| **R2** | Resolve **PMID / DOI / Europe PMC URL** when present in source metadata | Clickable literature links |
| **R3** | `GET /documents/{id}/chunks` or equivalent for audit trail | Reviewer can open source |
| **R4** | README + API: explicit **demo corpus, not clinical** disclaimer | Matches BioInsight tone |

---

## P1 — One platform story (with BioInsight)

| ID | Task | Depends on | Done when |
|----|------|------------|-----------|
| **R5** | Entity resolution: extracted genes → **ENSG**, diseases → **EFO/MONDO** (lookup table or API) | BioInsight 2.x | Same symbol maps to same id in both repos |
| **R6** | **`POST /ask` optional `gene_id` / `disease_id`** — bias retrieval toward graph-aligned entities | R5 | OpenAPI documented |
| **R7** | Extraction **provenance**: chunk id, extractor version, confidence on entities | — | Visible in graph explore or API |
| **R8** | Notebook: BRCA1 — BioInsight scores + kg-rag quotes side by side | BioInsight 4.4 | Single narrative demo |

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
- Full PRoH hypergraph replication
- Separate Neo4j instance required for production BioInsight (ports 7475/7688 stay isolated by design)

---

## Task pick order

1. **R1 → R4** (citations + trust)  
2. **R5 → R6** (IDs — after BioInsight 2.x)  
3. **R8** (demo notebook)  
4. **R9 → R11** (plan-aware)  
5. **R13+** if time

---

*Living doc — PRs reference task IDs (e.g. `R2`).*
