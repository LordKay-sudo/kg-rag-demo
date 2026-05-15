from fastapi import APIRouter, HTTPException

from app.db import get_session
from app.ingest.pipeline import ingest_document
from app.models.schemas import DocumentSummary, IngestResponse

router = APIRouter(tags=["documents"])


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


@router.post("/ingest/{document_id}", response_model=IngestResponse)
def ingest(document_id: str) -> IngestResponse:
    try:
        result = ingest_document(document_id)
    except FileNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return IngestResponse(**result)
