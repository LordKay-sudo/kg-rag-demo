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


class SubgraphNode(BaseModel):
    id: str
    label: str
    name: str | None = None


class SubgraphLink(BaseModel):
    source: str
    target: str
    type: str


class ExploreResponse(BaseModel):
    entity_id: str
    nodes: list[SubgraphNode]
    links: list[SubgraphLink]


class UploadResponse(BaseModel):
    document_id: str
    title: str
    status: str
