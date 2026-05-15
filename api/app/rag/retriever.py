from __future__ import annotations

from dataclasses import dataclass

from app.config import settings
from app.db import get_session
from app.ingest.embedder import cosine_similarity, embed_texts


@dataclass
class RetrievedChunk:
    chunk_id: str
    document_id: str
    text: str
    score: float


def retrieve_chunks(question: str, top_k: int | None = None) -> list[RetrievedChunk]:
    top_k = top_k or settings.top_k_chunks
    q_emb = embed_texts([question])[0]

    with get_session() as session:
        rows = session.run(
            """
            MATCH (c:Chunk)
            RETURN c.id AS chunk_id, c.document_id AS document_id,
                   c.text AS text, c.embedding AS embedding
            """
        ).data()

    scored: list[RetrievedChunk] = []
    for row in rows:
        if not row.get("embedding"):
            continue
        score = cosine_similarity(q_emb, row["embedding"])
        scored.append(
            RetrievedChunk(
                chunk_id=row["chunk_id"],
                document_id=row["document_id"],
                text=row["text"],
                score=score,
            )
        )

    scored.sort(key=lambda x: x.score, reverse=True)
    return scored[:top_k]
