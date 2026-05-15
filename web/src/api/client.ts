export interface Citation {
  chunk_id: string;
  document_id: string;
  snippet: string;
  score?: number | null;
}

export interface EntityRef {
  type: string;
  id: string;
}

export interface AskResponse {
  answer: string;
  citations: Citation[];
  entities: EntityRef[];
  subgraph: { nodes: unknown[]; edges: unknown[] };
}

export interface DocumentSummary {
  id: string;
  title: string;
  source: string;
  status: string;
  ingested_at: string | null;
}

async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init);
  if (!res.ok) throw new Error(await res.text() || `HTTP ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  ask: (question: string) =>
    fetchJson<AskResponse>("/api/v1/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    }),
  listDocuments: () => fetchJson<DocumentSummary[]>("/api/v1/documents"),
  health: () =>
    fetchJson<{ status: string; neo4j: boolean; llm_provider: string }>("/api/v1/health"),
};
