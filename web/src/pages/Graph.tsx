import { useEffect, useState } from "react";
import { Link, useNavigate, useParams, useSearchParams } from "react-router-dom";
import ForceGraphView from "../components/ForceGraphView";
import { api } from "../api/client";

export default function Graph() {
  const { entityId: routeId } = useParams<{ entityId: string }>();
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const [query, setQuery] = useState(routeId ?? searchParams.get("id") ?? "BRCA1");
  const [centerId, setCenterId] = useState(routeId ?? "BRCA1");
  const [nodes, setNodes] = useState<Awaited<ReturnType<typeof api.exploreGraph>>["nodes"]>([]);
  const [links, setLinks] = useState<Awaited<ReturnType<typeof api.exploreGraph>>["links"]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const load = async (id: string) => {
    if (!id.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const data = await api.exploreGraph(id.trim());
      setCenterId(data.entity_id);
      setNodes(data.nodes);
      setLinks(data.links);
      navigate(`/graph/${encodeURIComponent(data.entity_id)}`, { replace: true });
    } catch (e) {
      setError(e instanceof Error ? e.message : "Failed to load graph");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (routeId) {
      setQuery(routeId);
      load(routeId);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [routeId]);

  return (
    <>
      <h2 className="page-title">Graph explorer</h2>
      <p className="page-subtitle">
        One-hop neighborhood around a gene, disease, or drug extracted from the corpus.
      </p>

      <div className="explore-bar">
        <input
          className="explore-input"
          placeholder="Entity id e.g. BRCA1, breast_cancer, olaparib"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && load(query)}
        />
        <button className="btn" type="button" disabled={loading} onClick={() => load(query)}>
          {loading ? "Loading…" : "Explore"}
        </button>
      </div>

      <p className="hint">
        Try entities from <Link to="/">Ask</Link> answers, or open{" "}
        <Link to="/graph/BRCA1">BRCA1</Link>.
      </p>

      {error && <p className="error">{error}</p>}

      {!loading && nodes.length > 0 && (
        <section className="graph-section">
          <h3 className="graph-heading">Center: {centerId}</h3>
          <ForceGraphView centerId={centerId} nodes={nodes} links={links} />
        </section>
      )}
    </>
  );
}
