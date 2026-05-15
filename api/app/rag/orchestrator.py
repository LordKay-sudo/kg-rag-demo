from __future__ import annotations

import re

import httpx

from app.config import settings
from app.db import get_session
from app.rag.retriever import retrieve_chunks

CHUNK_CITE = re.compile(r"\[chunk:([^\]]+)\]")


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
            RETURN DISTINCT labels(e)[0] AS type, e.id AS id
            """,
            chunk_ids=chunk_ids,
        ).data()
    return [{"type": r["type"], "id": r["id"]} for r in rows]


def _subgraph(entities: list[dict]) -> dict:
    if not entities:
        return {"nodes": [], "edges": []}
    ids = [e["id"] for e in entities]
    with get_session() as session:
        nodes = session.run(
            """
            UNWIND $ids AS eid
            MATCH (n) WHERE n.id = eid
            RETURN DISTINCT labels(n)[0] AS label, n.id AS id
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
    return {"nodes": nodes, "edges": edges}


def ask(question: str) -> dict:
    chunks = retrieve_chunks(question)
    if not chunks or chunks[0].score < settings.min_retrieval_score:
        return {
            "answer": "I don't have enough evidence in the corpus to answer that question.",
            "citations": [],
            "entities": [],
            "subgraph": {"nodes": [], "edges": []},
        }

    template = (settings.prompts_dir / "answer_with_citations.txt").read_text(encoding="utf-8")
    prompt = template.format(context=_build_context(chunks), question=question)

    answer = ""
    if settings.llm_provider == "ollama":
        answer = _call_ollama(prompt)
    if not answer:
        answer = _fallback_answer(question, chunks)

    cited_ids = CHUNK_CITE.findall(answer) or [chunks[0].chunk_id]
    citations = [
        {
            "chunk_id": c.chunk_id,
            "document_id": c.document_id,
            "snippet": c.text[:300],
            "score": c.score,
        }
        for c in chunks
        if c.chunk_id in cited_ids or c == chunks[0]
    ][: settings.top_k_chunks]

    entities = _entities_from_chunks([c["chunk_id"] for c in citations])
    return {
        "answer": answer,
        "citations": citations,
        "entities": entities,
        "subgraph": _subgraph(entities),
    }
