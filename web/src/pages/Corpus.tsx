import { useEffect, useState } from "react";
import { api, type DocumentSummary } from "../api/client";

export default function Corpus() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<string | null>(null);

  useEffect(() => {
    Promise.all([api.listDocuments(), api.health()])
      .then(([documents, h]) => {
        setDocs(documents);
        setHealth(h.status);
      })
      .catch((e) => setError(e instanceof Error ? e.message : "Failed to load corpus"))
      .finally(() => setLoading(false));
  }, []);

  return (
    <>
      <h2 className="page-title">Corpus</h2>
      <p className="page-subtitle">
        Ingested biomedical-style abstracts used for entity extraction and retrieval.
      </p>

      {health && (
        <p className="hint" style={{ marginBottom: "1rem" }}>
          API status: <strong style={{ color: "var(--gene)" }}>{health}</strong>
        </p>
      )}

      {loading && <p className="hint">Loading documents…</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && (
        <div className="table-wrap">
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Source</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {docs.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ color: "var(--muted)" }}>
                    No documents yet. Run seed + ingest from the repo root.
                  </td>
                </tr>
              ) : (
                docs.map((d) => (
                  <tr key={d.id}>
                    <td>{d.id}</td>
                    <td>{d.title}</td>
                    <td>{d.source}</td>
                    <td>
                      <span className={`status status-${d.status === "ingested" ? "ingested" : "pending"}`}>
                        {d.status}
                      </span>
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
