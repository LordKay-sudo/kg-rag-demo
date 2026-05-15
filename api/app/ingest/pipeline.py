from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from app.config import settings
from app.db import get_session
from app.ingest.chunker import chunk_text
from app.ingest.embedder import embed_texts
from app.ingest.extractor import extract_entities


def ingest_document(document_id: str) -> dict:
    path = settings.documents_dir / f"{document_id}.txt"
    if not path.exists():
        raise FileNotFoundError(f"Document file not found: {path}")

    raw = path.read_text(encoding="utf-8")
    lines = raw.splitlines()
    title = lines[0].replace("Title: ", "") if lines else document_id
    body = "\n".join(lines[1:]).strip() or raw

    chunks = chunk_text(body, settings.chunk_size, settings.chunk_overlap)
    embeddings = embed_texts(chunks)

    with get_session() as session:
        session.run(
            """
            MERGE (d:Document {id: $id})
            SET d.title = $title, d.source = $source, d.status = 'ingesting'
            """,
            id=document_id,
            title=title,
            source=path.name,
        )

        session.run(
            """
            MATCH (d:Document {id: $doc_id})<-[:FROM_DOCUMENT]-(c:Chunk)
            DETACH DELETE c
            """,
            doc_id=document_id,
        )

        for idx, (text, emb) in enumerate(zip(chunks, embeddings)):
            chunk_id = f"{document_id}-chunk-{idx}"
            entities, relations = extract_entities(text)

            session.run(
                """
                MATCH (d:Document {id: $doc_id})
                CREATE (c:Chunk {
                    id: $chunk_id,
                    document_id: $doc_id,
                    text: $text,
                    index: $index,
                    embedding: $embedding
                })
                MERGE (c)-[:FROM_DOCUMENT]->(d)
                """,
                doc_id=document_id,
                chunk_id=chunk_id,
                text=text,
                index=idx,
                embedding=emb,
            )

            for ent in entities:
                label = ent.type
                session.run(
                    f"""
                    MERGE (e:{label} {{id: $id}})
                    WITH e
                    MATCH (c:Chunk {{id: $chunk_id}})
                    MERGE (c)-[:MENTIONS]->(e)
                    """,
                    id=ent.id,
                    chunk_id=chunk_id,
                )

            for rel in relations:
                session.run(
                    f"""
                    MERGE (s:{rel.source_type} {{id: $source_id}})
                    MERGE (t:{rel.target_type} {{id: $target_id}})
                    MERGE (s)-[r:{rel.relation}]->(t)
                    SET r.confidence = $confidence, r.evidence_chunk_id = $chunk_id
                    """,
                    source_id=rel.source_id,
                    target_id=rel.target_id,
                    confidence=rel.confidence,
                    chunk_id=chunk_id,
                )

        session.run(
            """
            MATCH (d:Document {id: $id})
            SET d.status = 'ingested', d.ingested_at = $ts
            """,
            id=document_id,
            ts=datetime.now(timezone.utc).isoformat(),
        )

    return {"document_id": document_id, "chunks": len(chunks), "status": "ingested"}


def ingest_all_pending() -> list[dict]:
    results = []
    for path in sorted(settings.documents_dir.glob("*.txt")):
        results.append(ingest_document(path.stem))
    return results
