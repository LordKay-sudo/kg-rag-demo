# Knowledge Graph RAG Demo

Prototype that extracts entities from text documents, stores them in **Neo4j** as a lightweight **knowledge graph**, and answers natural-language questions using **retrieval-augmented generation (RAG)** with citations back to graph nodes and source chunks.

Complements [BioInsight Graph](../bioinsight-graph/) by focusing on **unstructured → structured knowledge → grounded Q&A** — closer to “extract knowledge from datasets/documents and incorporate into a knowledge graph.”

---

## Goals

- Pipeline: **ingest docs → chunk → extract entities/relations → Neo4j → embed chunks → query with citations**
- Demonstrate **Python FastAPI**, **Neo4j**, **React + TypeScript**, and optional **local or API-based LLM**
- Reuse patterns from enterprise document/OCR/RAG work without claiming biomedical expertise

**Non-goals (MVP):** production-grade NER model training, multi-tenant auth, petabyte scale

---

## Tech stack

| Layer | Choice |
|-------|--------|
| Graph DB | Neo4j 5.x |
| API | Python 3.11+, FastAPI, Pydantic |
| Extraction | Rule-based + optional `spaCy` **or** LLM structured output (OpenAI/Anthropic/Bedrock — env-driven) |
| Embeddings | `sentence-transformers` (local) **or** provider API |
| Vector store | Neo4j vector index **or** pgvector/SQLite-vec for simplicity |
| LLM | Configurable: Ollama (local), OpenAI, Anthropic |
| Frontend | React 18, TypeScript, Vite |
| Infra | Docker Compose |

---

## Architecture

```text
┌──────────────┐     ┌─────────────────┐     ┌──────────────┐
│  Documents   │     │  Ingest worker  │     │   Neo4j      │
│  PDF/TXT/MD  │ ──► │  chunk + extract│ ──► │  KG + chunks │
└──────────────┘     └────────┬────────┘     └──────┬───────┘
                              │ embed              │
                              ▼                    │
                     ┌─────────────────┐           │
                     │  Vector index   │           │
                     └────────┬────────┘           │
                              │                    │
                     ┌────────▼────────┐           │
                     │  RAG orchestrator│ ◄────────┘
                     │  (retrieve+LLM)  │
                     └────────┬────────┘
                              │
                     ┌────────▼────────┐
                     │  React UI       │
                     │  Ask + graph    │
                     └─────────────────┘
```

---

## Domain choice (pick one for MVP)

Use a **small, consistent** domain so extraction rules stay simple:

| Domain | Example docs | Entity types |
|--------|----------------|--------------|
| **Biomedical abstracts** (recommended) | 20–50 PubMed-style `.txt` stubs or open abstracts | `Gene`, `Disease`, `Drug`, `Publication` |
| Internal-style SOPs | Synthetic ops docs | `Process`, `System`, `Role` |
| Your portfolio | README + project docs | `Project`, `Technology`, `Concept` |

**Recommendation:** biomedical-flavored stub corpus in `data/documents/` (you write 10 short synthetic abstracts OR download open summaries with clear license).

---

## Graph schema (MVP)

```cypher
(:Document {id, title, source, ingested_at})
(:Chunk {id, document_id, text, index, embedding_id})
(:Gene {id, symbol})
(:Disease {id, name})
(:Drug {id, name})

(:Chunk)-[:FROM_DOCUMENT]->(:Document)
(:Chunk)-[:MENTIONS]->(:Gene|:Disease|:Drug)
(:Gene)-[:ASSOCIATED_WITH {confidence, evidence_chunk_id}]->(:Disease)
(:Drug)-[:TREATS {confidence}]->(:Disease)
```

**Vector:** store embedding on `:Chunk` or separate vector DB keyed by `chunk_id`.

---

## RAG flow (MVP)

1. User asks a question in UI
2. Embed question → retrieve top-k **chunks** (and optionally expand via 1-hop graph)
3. Build prompt: question + chunk texts + optional triples from Neo4j
4. LLM generates answer with **citation IDs** (`[chunk:abc]`, `[gene:XYZ]`)
5. UI shows answer + linked sources + mini graph of cited nodes

**Guardrails:**

- If retrieval score below threshold → “I don’t have enough evidence in the corpus.”
- Never invent PMIDs/DOIs; only cite ingested `Document` ids

---

## API endpoints (MVP)

Base: `/api/v1`

| Method | Path | Description |
|--------|------|-------------|
| POST | `/documents` | Upload or register document path |
| POST | `/ingest/{document_id}` | Chunk, extract, embed, write graph |
| GET | `/documents` | List ingested docs + status |
| POST | `/ask` | Body: `{ "question": "..." }` → answer + citations + subgraph |
| GET | `/graph/explore?entity_id=` | Subgraph around entity |
| GET | `/health` | API + Neo4j + optional LLM reachability |

**Example `/ask` response shape:**

```json
{
  "answer": "Gene BRCA1 is associated with breast cancer in document doc-001.",
  "citations": [
    { "chunk_id": "chunk-12", "document_id": "doc-001", "snippet": "..." }
  ],
  "entities": [
    { "type": "Gene", "id": "BRCA1" },
    { "type": "Disease", "id": "breast_cancer" }
  ],
  "subgraph": { "nodes": [], "edges": [] }
}
```

---

## Frontend (MVP)

**Views:**

1. **Upload / ingest** — drop `.txt`/`.md`, trigger ingest, show progress
2. **Ask** — chat-style Q&A with expandable citations
3. **Graph explorer** — click entity from answer → neighbors
4. **Corpus** — list documents, re-ingest, delete (dev only)

---

## Repository structure

```text
kg-rag-demo/
├── README.md
├── LICENSE
├── docker-compose.yml
├── .env.example
├── api/
│   ├── app/
│   │   ├── main.py
│   │   ├── config.py
│   │   ├── db.py
│   │   ├── ingest/
│   │   │   ├── chunker.py
│   │   │   ├── extractor.py
│   │   │   └── embedder.py
│   │   ├── rag/
│   │   │   ├── retriever.py
│   │   │   └── orchestrator.py
│   │   └── routers/
│   └── tests/
├── scripts/
│   ├── seed_documents.py
│   └── neo4j/init.cypher
├── web/
│   └── src/
├── data/
│   └── documents/          # sample corpus
└── prompts/
    └── answer_with_citations.txt
```

---

## Configuration

`.env.example`:

```env
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=changeme

# LLM (choose one)
LLM_PROVIDER=ollama          # ollama | openai | anthropic
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.2
# OPENAI_API_KEY=
# ANTHROPIC_API_KEY=

EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
CHUNK_SIZE=500
CHUNK_OVERLAP=80
TOP_K_CHUNKS=5
```

---

## Getting started

### Prerequisites

- Docker (Neo4j)
- Python 3.11+
- Node.js 20+
- Optional: [Ollama](https://ollama.com/) for local LLM

### Quick path (after scaffold exists)

```bash
docker compose up -d neo4j
cp .env.example .env

cd api && pip install -r requirements.txt
uvicorn app.main:app --reload

# another terminal
cd web && npm install && npm run dev

# seed sample docs + ingest
python scripts/seed_documents.py
curl -X POST http://localhost:8000/api/v1/ingest/doc-001
```

---

## Extraction strategies (implement in order)

1. **Rule/regex MVP** — gene symbols `[A-Z][A-Z0-9]+`, disease phrases from a small dictionary
2. **spaCy** — `en_core_sci_sm` or generic `en_core_web_sm` for entities
3. **LLM structured JSON** — single prompt: “return entities and relations from this chunk”

Start with (1) so the graph populates before tuning quality.

---

## Testing

- Unit tests: chunker, citation parser, retriever ranking
- Integration: ingest one doc → `POST /ask` returns ≥1 citation
- Optional: golden-file tests for 3 fixed questions on seed corpus

---

## Development roadmap

| Phase | Deliverable |
|-------|-------------|
| **0** | Scaffold, Neo4j, Document/Chunk schema |
| **1** | Chunk + ingest API + list documents |
| **2** | Rule-based extractor → Neo4j MENTIONS edges |
| **3** | Embeddings + vector search |
| **4** | RAG `/ask` with Ollama or mock LLM |
| **5** | React Ask UI + citation panels |
| **6** | Graph explorer + Docker Compose + README demo GIF |

---

## MVP checklist

- [ ] ≥10 seed documents in `data/documents/`
- [ ] Ingest creates Chunks + at least one entity type in Neo4j
- [ ] `/ask` returns answer + ≥1 citation for seeded questions
- [ ] UI shows answer and source snippets
- [ ] README documents LLM provider setup and limitations
- [ ] No secrets in git; `.env` gitignored

---

## Portfolio blurb

> Demonstrates unstructured document ingestion, entity/relation extraction into Neo4j, vector retrieval, and citation-grounded Q&A via FastAPI and React — a minimal research-knowledge pipeline analogous to incorporating extracted knowledge into a queryable graph.

---

## Relation to BioInsight Graph

| Project | Focus |
|---------|--------|
| **bioinsight-graph** | Structured public datasets → graph → explore |
| **kg-rag-demo** | Unstructured text → graph + embeddings → Q&A |

Link both repos in your GitHub profile README.

---

## License

MIT (update if you choose otherwise)
