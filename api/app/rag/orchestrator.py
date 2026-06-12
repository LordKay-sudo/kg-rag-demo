from __future__ import annotations

import re

import httpx

from app.config import settings
from app.db import get_session
from app.identifiers import resolve_disease_id, resolve_gene_id
from app.rag.query_expand import expand_question
from app.rag.retriever import retrieve_chunks
from app.references import resolve_reference_url

CHUNK_CITE = re.compile(r"\[chunk:([^\]]+)\]")

# Score boost applied to chunks that mention a caller-specified entity (R6).
ENTITY_BIAS_BOOST = 0.15


def _build_context(chunks) -> str:
    parts = []
    for c in chunks:
        parts.append(f"[chunk:{c.chunk_id}] (doc={c.document_id}, score={c.score:.2f})\n{c.text}")
    return "\n\n".join(parts)


def _fallback_answer(question: str, chunks) -> str:
    if not chunks:
        return "I don't have enough evidence in the corpus to answer that question."
    top = chunks[0]
    return (
        f"Based on the retrieved evidence, see [chunk:{top.chunk_id}]. "
        f"The source discusses: {top.text[:280]}..."
    )


def _call_ollama(prompt: str) -> str:
    url = f"{settings.ollama_base_url.rstrip('/')}/api/generate"
    payload = {"model": settings.ollama_model, "prompt": prompt, "stream": False}
    try:
        with httpx.Client(timeout=120.0) as client:
            r = client.post(url, json=payload)
            r.raise_for_status()
            return r.json().get("response", "").strip()
    except Exception:
        return ""


def _entities_from_chunks(chunk_ids: list[str]) -> list[dict]:
    if not chunk_ids:
        return []
    with get_session() as session:
        rows = session.run(
            """
            UNWIND $chunk_ids AS cid
            MATCH (c:Chunk {id: cid})-[:MENTIONS]->(e)
            RETURN DISTINCT labels(e)[0] AS type, e.id AS id, e.ontology_id AS ontology_id
            """,
            chunk_ids=chunk_ids,
        ).data()
    return [
        {"type": r["type"], "id": r["id"], "ontology_id": r.get("ontology_id")}
        for r in rows
    ]


def _documents_meta(document_ids: list[str]) -> dict[str, dict]:
    if not document_ids:
        return {}
    with get_session() as session:
        rows = session.run(
            """
            UNWIND $ids AS did
            MATCH (d:Document {id: did})
            RETURN d.id AS id, d.title AS title, d.source AS source,
                   d.pmid AS pmid, d.doi AS doi, d.url AS url
            """,
            ids=document_ids,
        ).data()
    return {r["id"]: r for r in rows}


def _bias_chunk_ids(gene_id: str | None, disease_id: str | None) -> set[str]:
    """Chunk ids that mention the caller-specified gene/disease (R6).

    Accepts either the extractor id (symbol / slug) or the shared ontology id
    (ENSG / EFO / MONDO); matches against both ``id`` and ``ontology_id``.
    """
    targets: list[str] = []
    for raw in (gene_id, disease_id):
        if not raw:
            continue
        targets.append(raw)
        upper = raw.upper()
        targets.append(upper)
        # Map a bare symbol/slug to its ontology id and vice versa.
        resolved = resolve_gene_id(raw) or resolve_disease_id(raw)
        if resolved:
            targets.append(resolved)

    targets = list({t for t in targets if t})
    if not targets:
        return set()

    with get_session() as session:
        rows = session.run(
            """
            MATCH (c:Chunk)-[:MENTIONS]->(e)
            WHERE e.id IN $targets OR e.ontology_id IN $targets
            RETURN DISTINCT c.id AS chunk_id
            """,
            targets=targets,
        ).data()
    return {r["chunk_id"] for r in rows}


def _subgraph(entities: list[dict]) -> dict:
    if not entities:
        return {"nodes": [], "edges": []}
    ids = [e["id"] for e in entities]
    with get_session() as session:
        nodes = session.run(
            """
            UNWIND $ids AS eid
            MATCH (n) WHERE n.id = eid
            RETURN DISTINCT labels(n)[0] AS label, n.id AS id,
                   coalesce(n.symbol, n.name, n.title, n.id) AS name
            """,
            ids=ids,
        ).data()
        edges = session.run(
            """
            UNWIND $ids AS eid
            MATCH (a)-[r]->(b)
            WHERE a.id = eid OR b.id = eid
            RETURN DISTINCT a.id AS source, type(r) AS type, b.id AS target
            LIMIT 50
            """,
            ids=ids,
        ).data()
    return {
        "nodes": [{"label": n["label"], "id": n["id"], "name": n.get("name")} for n in nodes],
        "edges": edges,
    }


def _empty_response(*, expanded_question: str | None = None) -> dict:
    return {
        "answer": "I don't have enough evidence in the corpus to answer that question.",
        "citations": [],
        "entities": [],
        "subgraph": {"nodes": [], "edges": []},
        "insufficient_evidence": True,
        "expanded_question": expanded_question,
    }


def ask(
    question: str,
    gene_id: str | None = None,
    disease_id: str | None = None,
    *,
    weak_graph_evidence: bool = False,
    compact: bool = False,
) -> dict:
    expanded = expand_question(question)
    top_k = settings.compact_top_k if compact else settings.top_k_chunks
    snippet_len = settings.compact_snippet_chars if compact else 300
    min_score = settings.min_retrieval_score

    if weak_graph_evidence:
        top_k = max(top_k, settings.widen_top_k)
        min_score = settings.widen_min_retrieval_score

    chunks = retrieve_chunks(expanded, top_k=top_k)

    # Bias retrieval toward graph-aligned entities when the caller pins one (R6).
    if chunks and (gene_id or disease_id):
        biased_ids = _bias_chunk_ids(gene_id, disease_id)
        if biased_ids:
            for c in chunks:
                if c.chunk_id in biased_ids:
                    c.score = min(1.0, c.score + ENTITY_BIAS_BOOST)
            chunks.sort(key=lambda x: x.score, reverse=True)

    insufficient = not chunks or chunks[0].score < settings.min_retrieval_score
    admit_score = settings.widen_min_retrieval_score if compact else min_score
    if not chunks or chunks[0].score < admit_score:
        return _empty_response(expanded_question=expanded)

    template = (settings.prompts_dir / "answer_with_citations.txt").read_text(encoding="utf-8")
    prompt = template.format(context=_build_context(chunks), question=question)

    answer = ""
    if settings.llm_provider == "ollama":
        answer = _call_ollama(prompt)
    if not answer:
        answer = _fallback_answer(question, chunks)

    if insufficient and compact:
        answer = (
            f"[Partial evidence — top retrieval score {chunks[0].score:.2f}] "
            + answer
        )

    cited_ids = CHUNK_CITE.findall(answer) or [chunks[0].chunk_id]
    cite_cap = settings.compact_top_k if compact else settings.top_k_chunks
    cited_chunks = [
        c for c in chunks if c.chunk_id in cited_ids or c == chunks[0]
    ][:cite_cap]

    docs_meta = _documents_meta(list({c.document_id for c in cited_chunks}))
    citations = []
    for c in cited_chunks:
        meta = docs_meta.get(c.document_id, {})
        title = meta.get("title")
        citations.append(
            {
                "chunk_id": c.chunk_id,
                "document_id": c.document_id,
                "document_title": title,
                "source": meta.get("source"),
                "snippet": c.text[:snippet_len],
                "score": c.score,
                "pmid": meta.get("pmid"),
                "doi": meta.get("doi"),
                "reference_url": resolve_reference_url(
                    url=meta.get("url"),
                    doi=meta.get("doi"),
                    pmid=meta.get("pmid"),
                    title=title,
                ),
            }
        )

    entities = _entities_from_chunks([c["chunk_id"] for c in citations])
    return {
        "answer": answer,
        "citations": citations,
        "entities": entities,
        "subgraph": _subgraph(entities),
        "insufficient_evidence": insufficient,
        "expanded_question": expanded,
    }
