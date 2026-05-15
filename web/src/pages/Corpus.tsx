import { useCallback, useEffect, useRef, useState } from "react";
import { api, type DocumentSummary } from "../api/client";

export default function Corpus() {
  const [docs, setDocs] = useState<DocumentSummary[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [health, setHealth] = useState<string | null>(null);
  const [busyId, setBusyId] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [documents, h] = await Promise.all([api.listDocuments(), api.health()]);
      setDocs(documents);
      setHealth(h.status);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load corpus");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh]);

  const ingestOne = async (docId: string) => {
    setBusyId(docId);
    setMessage(null);
    try {
      const res = await api.ingestDocument(docId);
      setMessage(`Ingested ${docId}: ${res.chunks} chunks`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Ingest failed");
    } finally {
      setBusyId(null);
    }
  };

  const ingestAllPending = async () => {
    const pending = docs.filter((d) => d.status !== "ingested");
    if (pending.length === 0) {
      setMessage("No pending documents.");
      return;
    }
    setBusyId("__all__");
    setMessage(null);
    try {
      for (const d of pending) {
        await api.ingestDocument(d.id);
      }
      setMessage(`Ingested ${pending.length} document(s).`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Batch ingest failed");
    } finally {
      setBusyId(null);
    }
  };

  const onUpload = async (file: File | null) => {
    if (!file) return;
    setUploading(true);
    setError(null);
    setMessage(null);
    try {
      const res = await api.uploadDocument(file);
      setMessage(`Uploaded ${res.document_id}: ${res.title}`);
      await refresh();
    } catch (e) {
      setError(e instanceof Error ? e.message : "Upload failed");
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = "";
    }
  };

  return (
    <>
      <h2 className="page-title">Corpus</h2>
      <p className="page-subtitle">
        Upload `.txt` or `.md` abstracts, then ingest to extract entities and embeddings.
      </p>

      {health && (
        <p className="hint" style={{ marginBottom: "1rem" }}>
          API status: <strong style={{ color: "var(--gene)" }}>{health}</strong>
        </p>
      )}

      <div className="upload-panel">
        <input
          ref={fileRef}
          type="file"
          accept=".txt,.md"
          className="file-input"
          onChange={(e) => onUpload(e.target.files?.[0] ?? null)}
        />
        <button
          className="btn"
          type="button"
          disabled={uploading}
          onClick={() => fileRef.current?.click()}
        >
          {uploading ? "Uploading…" : "Upload document"}
        </button>
        <button
          className="btn"
          type="button"
          style={{ background: "transparent", border: "1px solid var(--border)", color: "var(--muted)" }}
          disabled={busyId === "__all__" || loading}
          onClick={ingestAllPending}
        >
          {busyId === "__all__" ? "Ingesting…" : "Ingest all pending"}
        </button>
      </div>

      {message && <p className="hint" style={{ color: "var(--gene)" }}>{message}</p>}
      {loading && <p className="hint">Loading documents…</p>}
      {error && <p className="error">{error}</p>}

      {!loading && !error && (
        <div className="table-wrap" style={{ marginTop: "1rem" }}>
          <table>
            <thead>
              <tr>
                <th>ID</th>
                <th>Title</th>
                <th>Source</th>
                <th>Status</th>
                <th>Actions</th>
              </tr>
            </thead>
            <tbody>
              {docs.length === 0 ? (
                <tr>
                  <td colSpan={5} style={{ color: "var(--muted)" }}>
                    No documents yet. Upload a file or run the seed scripts.
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
                    <td>
                      <button
                        className="btn btn-sm"
                        type="button"
                        disabled={busyId !== null}
                        onClick={() => ingestOne(d.id)}
                      >
                        {busyId === d.id ? "…" : d.status === "ingested" ? "Re-ingest" : "Ingest"}
                      </button>
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
