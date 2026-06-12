from fastapi import APIRouter

from app.models.schemas import AskRequest, AskResponse
from app.rag.orchestrator import ask

router = APIRouter(tags=["rag"])


@router.post("/ask", response_model=AskResponse)
def ask_question(body: AskRequest) -> AskResponse:
    result = ask(body.question, gene_id=body.gene_id, disease_id=body.disease_id)
    return AskResponse(**result)
