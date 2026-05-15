from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    status: str
    neo4j: bool
    llm_provider: str


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    snippet: str
    score: float | None = None


class EntityRef(BaseModel):
    type: str
    id: str


class AskResponse(BaseModel):
    answer: str
    citations: list[Citation]
    entities: list[EntityRef]
    subgraph: dict


class DocumentSummary(BaseModel):
    id: str
    title: str
    source: str
    status: str
    ingested_at: str | None = None


class IngestResponse(BaseModel):
    document_id: str
    chunks: int
    status: str
