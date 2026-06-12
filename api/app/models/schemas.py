from pydantic import BaseModel, Field


DISCLAIMER = (
    "Demo corpus of synthetic biomedical-style abstracts — not real publications, "
    "not clinical-grade. Associations are illustrative, not causal. See PROVENANCE.md."
)


class HealthResponse(BaseModel):
    status: str
    neo4j: bool
    llm_provider: str
    disclaimer: str = DISCLAIMER


class AskRequest(BaseModel):
    question: str = Field(..., min_length=3)
    gene_id: str | None = Field(
        default=None,
        description="Optional Ensembl ENSG id or gene symbol to bias retrieval toward "
        "graph-aligned entities (roadmap R6).",
    )
    disease_id: str | None = Field(
        default=None,
        description="Optional EFO/MONDO id or disease slug to bias retrieval (roadmap R6).",
    )


class Citation(BaseModel):
    chunk_id: str
    document_id: str
    document_title: str | None = None
    source: str | None = None
    snippet: str
    score: float | None = None
    pmid: str | None = None
    doi: str | None = None
    reference_url: str | None = None


class EntityRef(BaseModel):
    type: str
    id: str
    ontology_id: str | None = None
    confidence: float | None = None
    extractor_version: str | None = None


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


class ChunkDetail(BaseModel):
    chunk_id: str
    index: int
    text: str
    entities: list[EntityRef] = []


class DocumentChunksResponse(BaseModel):
    document_id: str
    title: str | None = None
    source: str | None = None
    pmid: str | None = None
    doi: str | None = None
    reference_url: str | None = None
    chunk_count: int
    chunks: list[ChunkDetail]


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
