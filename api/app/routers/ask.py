from fastapi import APIRouter

from app.models.schemas import AskPlanResponse, AskRequest, AskResponse
from app.rag.orchestrator import ask
from app.rag.planner import plan_question

router = APIRouter(tags=["rag"])


@router.post("/ask/plan", response_model=AskPlanResponse)
def ask_plan(body: AskRequest) -> AskPlanResponse:
    result = plan_question(
        body.question,
        gene_id=body.gene_id,
        disease_id=body.disease_id,
    )
    return AskPlanResponse(**result)


@router.post("/ask", response_model=AskResponse)
def ask_question(body: AskRequest) -> AskResponse:
    widen = body.weak_graph_evidence
    if not widen and body.gene_id:
        from app.rag.graph_bridge import graph_evidence_is_weak

        widen = graph_evidence_is_weak(body.gene_id)

    result = ask(
        body.question,
        gene_id=body.gene_id,
        disease_id=body.disease_id,
        weak_graph_evidence=widen,
        compact=body.compact,
    )
    return AskResponse(**result)
