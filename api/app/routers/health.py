from fastapi import APIRouter

from app.config import settings
from app.db import check_connectivity
from app.models.schemas import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
def health() -> HealthResponse:
    neo4j_ok = check_connectivity()
    status = "ok" if neo4j_ok else "degraded"
    return HealthResponse(status=status, neo4j=neo4j_ok, llm_provider=settings.llm_provider)
