import re
import uuid
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile

from app.config import settings
from app.db import get_session
from app.ingest.metadata import parse_document
from app.ingest.pipeline import ingest_document
from app.models.schemas import (
    ChunkDetail,
    DocumentChunksResponse,
    DocumentSummary,
    EntityRef,
    IngestResponse,
    UploadResponse,
)
from app.references import resolve_reference_url

router = APIRouter(tags=["documents"])

ALLOWED_SUFFIXES = {".txt", ".md"}


def _slug(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_")
    return slug[:48] or "doc"


def _unique_doc_id(base: str) -> str:
    candidate = _slug(base)
    if not (settings.documents_dir / f"{candidate}.txt").exists():
        return candidate
    return f"{candidate}_{uuid.uuid4().hex[:6]}"


def _write_document_file(doc_id: str, meta) -> Path:
    settings.documents_dir.mkdir(parents=True, exist_ok=True)
    path = settings.documents_dir / f"{doc_id}.txt"
    header = [f"Title: {meta.title}"]
    if meta.source:
        header.append(f"Source: {meta.source}")
    if meta.pmid:
        header.append(f"PMID: {meta.pmid}")
    if meta.doi:
        header.append(f"DOI: {meta.doi}")
    if meta.url:
        header.append(f"URL: {meta.url}")
    path.write_text("\n".join(header) + f"\n\n{meta.body}\n", encoding="utf-8")
    return path


@router.get("/documents", response_model=list[DocumentSummary])
def list_documents() -> list[DocumentSummary]:
    with get_session() as session:
        rows = session.run(
            """
            MATCH (d:Document)
            RETURN d.id AS id, d.title AS title, d.source AS source,
                   coalesce(d.status, 'pending') AS status,
                   d.ingested_at AS ingested_at
            ORDER BY d.id
            """
        ).data()
    return [DocumentSummary(**r) for r in rows]


@router.post("/documents", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)) -> UploadResponse:
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SUFFIXES:
        raise HTTPException(status_code=400, detail="Only .txt and .md files are supported")

    raw = (await file.read()).decode("utf-8")
    fallback_title = Path(file.filename or "upload.txt").stem.replace("_", " ").replace("-", " ").title()
    meta = parse_document(raw, fallback_title=fallback_title)
    if not meta.body:
        raise HTTPException(status_code=400, detail="Document body is empty")

    doc_id = _unique_doc_id(Path(file.filename or meta.title).stem)
    path = _write_document_file(doc_id, meta)

    with get_session() as session:
        session.run(
            """
            MERGE (d:Document {id: $id})
            SET d.title = $title,
                d.source = $source,
                d.pmid = $pmid,
                d.doi = $doi,
                d.url = $url,
                d.status = 'pending',
                d.ingested_at = null
            """,
            id=doc_id,
            title=meta.title,
            source=meta.source or path.name,
            pmid=meta.pmid,
            doi=meta.doi,
            url=meta.url,
        )

    return UploadResponse(document_id=doc_id, title=meta.title, status="pending")


@router.get("/documents/{document_id}/chunks", response_model=DocumentChunksResponse)
def get_document_chunks(document_id: str) -> DocumentChunksResponse:
    """Audit trail (roadmap R3): every chunk + extracted entities behind a citation."""
    with get_session() as session:
        doc = session.run(
            """
            MATCH (d:Document {id: $id})
            RETURN d.id AS id, d.title AS title, d.source AS source,
                   d.pmid AS pmid, d.doi AS doi, d.url AS url
            """,
            id=document_id,
        ).single()
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found")

        rows = session.run(
            """
            MATCH (c:Chunk {document_id: $id})
            OPTIONAL MATCH (c)-[:MENTIONS]->(e)
            RETURN c.id AS chunk_id, c.index AS index, c.text AS text,
                   collect(DISTINCT {type: labels(e)[0], id: e.id,
                                     ontology_id: e.ontology_id}) AS entities
            ORDER BY c.index
            """,
            id=document_id,
        ).data()

    chunks = [
        ChunkDetail(
            chunk_id=r["chunk_id"],
            index=r["index"] if r["index"] is not None else 0,
            text=r["text"],
            entities=[
                EntityRef(type=e["type"], id=e["id"], ontology_id=e.get("ontology_id"))
                for e in r["entities"]
                if e.get("type") and e.get("id")
            ],
        )
        for r in rows
    ]

    return DocumentChunksResponse(
        document_id=doc["id"],
        title=doc.get("title"),
        source=doc.get("source"),
        pmid=doc.get("pmid"),
        doi=doc.get("doi"),
        reference_url=resolve_reference_url(
            url=doc.get("url"), doi=doc.get("doi"), pmid=doc.get("pmid"), title=doc.get("title")
        ),
        chunk_count=len(chunks),
        chunks=chunks,
    )


@router.post("/ingest/{document_id}", response_model=IngestResponse)
def ingest(document_id: str) -> IngestResponse:
    try:
        result = ingest_document(document_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return IngestResponse(**result)
