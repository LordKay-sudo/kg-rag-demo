import { useState } from "react";
import { Link } from "react-router-dom";
import ForceGraphView from "../components/ForceGraphView";
import { api, subgraphFromAsk, type AskResponse } from "../api/client";

const EXAMPLES = [
  "What is the link between BRCA1 and breast cancer?",
  "Which drugs are mentioned for melanoma?",
  "How does CFTR relate to cystic fibrosis?",
];

export default function Ask() {
  const [question, setQuestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AskResponse | null>(null);

  const submit = async (q: string) => {
    if (q.trim().length < 3) return;
    setLoading(true);
    setError(null);
    setResult(null);
    try {
      const res = await api.ask(q.trim());
      setResult(res);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Request failed");
    } finally {
      setLoading(false);
    }
  };

  const inlineGraph = result ? subgraphFromAsk(result) : null;

  return (
    <>
      <h2 className="page-title">Ask the knowledge graph</h2>
      <p className="page-subtitle">
        Retrieval-augmented answers with citations from ingested biomedical abstracts.
      </p>

      <div className="ask-panel">
        <textarea
          className="ask-input"
          placeholder="Ask a question about genes, diseases, or drugs in the corpus…"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
        />
        <div className="ask-actions">
          <button className="btn" type="button" disabled={loading} onClick={() => submit(question)}>
            {loading ? "Thinking…" : "Ask"}
          </button>
          <span className="hint">Uses vector search + optional Ollama LLM</span>
        </div>
        <div style={{ marginTop: "0.75rem", display: "flex", flexWrap: "wrap", gap: "0.5rem" }}>
          {EXAMPLES.map((ex) => (
            <button
              key={ex}
              type="button"
              className="btn"
              style={{
                background: "transparent",
                border: "1px solid var(--border)",
                color: "var(--muted)",
                fontSize: "0.8rem",
              }}
              onClick={() => {
                setQuestion(ex);
                submit(ex);
              }}
            >
              {ex}
            </button>
          ))}
        </div>

        {error && <p className="error" style={{ marginTop: "1rem" }}>{error}</p>}

        {result && (
          <div className="answer-box">
            <h3>Answer</h3>
            <p>{result.answer}</p>
            {result.entities.length > 0 && (
              <div className="entity-tags">
                {result.entities.map((e) => (
                  <Link
                    key={`${e.type}-${e.id}`}
                    to={`/graph/${encodeURIComponent(e.id)}`}
                    className="tag tag-link"
                  >
                    {e.type}: {e.id}
                  </Link>
                ))}
              </div>
            )}
            {result.citations.length > 0 && (
              <>
                <h3 style={{ marginTop: "1rem" }}>Sources</h3>
                {result.citations.map((c) => (
                  <div key={c.chunk_id} className="citation">
                    <div className="citation-meta">
                      {c.document_id} · chunk {c.chunk_id}
                      {c.score != null ? ` · score ${c.score.toFixed(2)}` : ""}
                    </div>
                    {c.snippet}
                  </div>
                ))}
              </>
            )}
            {inlineGraph && inlineGraph.nodes.length > 0 && (
              <section className="graph-section" style={{ marginTop: "1.25rem" }}>
                <h3>Related subgraph</h3>
                <ForceGraphView
                  centerId={inlineGraph.entity_id}
                  nodes={inlineGraph.nodes}
                  links={inlineGraph.links}
                />
                <p className="hint" style={{ marginTop: "0.5rem" }}>
                  <Link to={`/graph/${encodeURIComponent(inlineGraph.entity_id)}`}>
                    Open full explorer →
                  </Link>
                </p>
              </section>
            )}
          </div>
        )}
      </div>
    </>
  );
}
