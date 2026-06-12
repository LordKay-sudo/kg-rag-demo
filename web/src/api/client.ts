export interface Citation {
  chunk_id: string;
  document_id: string;
  document_title?: string | null;
  source?: string | null;
  snippet: string;
  score?: number | null;
  pmid?: string | null;
  doi?: string | null;
  reference_url?: string | null;
}

export interface EntityRef {
  type: string;
  id: string;
  ontology_id?: string | null;
}

export interface SubgraphNode {
  id: string;
  label: string;
  name?: string | null;
}

export interface SubgraphLink {
  source: string;
  target: string;
  type: string;
}

export interface ExploreResponse {
  entity_id: string;
  nodes: SubgraphNode[];
  links: SubgraphLink[];
}

export interface AskResponse {
  answer: string;
  citations: Citation[];
  entities: EntityRef[];
  subgraph: {
    nodes: Array<{ label: string; id: string; name?: string }>;
    edges: Array<{ source: string; target: string; type: string }>;
  };
  insufficient_evidence?: boolean;
  expanded_question?: string | null;
}

export interface AskPlanStep {
  sub_query: string;
  entity_type?: string | null;
  entity_id?: string | null;
  ontology_id?: string | null;
}

export interface AskPlanResponse {
  question: string;
  expanded_question: string;
  intent: string;
  steps: AskPlanStep[];
  suggested_gene_id?: string | null;
  suggested_disease_id?: string | null;
  widen_retrieval: boolean;
}

export interface DocumentSummary {
  id: string;
  title: string;
  source: string;
  status: string;
  ingested_at: string | null;
}

export interface UploadResponse {
  document_id: string;
  title: string;
  status: string;
}

export interface IngestResponse {
  document_id: string;
  chunks: number;
  status: string;
}

export interface ChunkDetail {
  chunk_id: string;
  index: number;
  text: string;
  entities: EntityRef[];
}

export interface DocumentChunksResponse {
  document_id: string;
  title?: string | null;
  source?: string | null;
  pmid?: string | null;
  doi?: string | null;
  reference_url?: string | null;
  chunk_count: number;
  chunks: ChunkDetail[];
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) {
    let detail = `HTTP ${res.status}`;
    try {
      const body = (await res.json()) as { detail?: string };
      if (body.detail) detail = body.detail;
    } catch {
      const text = await res.text();
      if (text) detail = text;
    }
    throw new Error(detail);
  }
  return res.json() as Promise<T>;
}

export function subgraphFromAsk(result: AskResponse): ExploreResponse | null {
  const nodes = (result.subgraph?.nodes ?? []).map((n) => ({
    id: n.id,
    label: n.label,
    name: n.name ?? n.id,
  }));
  const links = (result.subgraph?.edges ?? []).map((e) => ({
    source: e.source,
    target: e.target,
    type: e.type,
  }));
  if (nodes.length === 0) return null;
  const centerId = result.entities[0]?.id ?? nodes[0].id;
  return { entity_id: centerId, nodes, links };
}

export const api = {
  ask: (
    question: string,
    opts?: { gene_id?: string; disease_id?: string; weak_graph_evidence?: boolean; compact?: boolean }
  ) =>
    fetchJson<AskResponse>("/api/v1/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, ...opts }),
    }),
  askPlan: (question: string, opts?: { gene_id?: string; disease_id?: string }) =>
    fetchJson<AskPlanResponse>("/api/v1/ask/plan", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question, ...opts }),
    }),
  listDocuments: () => fetchJson<DocumentSummary[]>("/api/v1/documents"),
  documentChunks: (documentId: string) =>
    fetchJson<DocumentChunksResponse>(
      `/api/v1/documents/${encodeURIComponent(documentId)}/chunks`
    ),
  uploadDocument: (file: File) => {
    const form = new FormData();
    form.append("file", file);
    return fetchJson<UploadResponse>("/api/v1/documents", { method: "POST", body: form });
  },
  ingestDocument: (documentId: string) =>
    fetchJson<IngestResponse>(`/api/v1/ingest/${encodeURIComponent(documentId)}`, {
      method: "POST",
    }),
  exploreGraph: (entityId: string) =>
    fetchJson<ExploreResponse>(
      `/api/v1/graph/explore?entity_id=${encodeURIComponent(entityId)}`
    ),
  health: () =>
    fetchJson<{ status: string; neo4j: boolean; llm_provider: string; disclaimer: string }>(
      "/api/v1/health"
    ),
};
