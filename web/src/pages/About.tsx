export default function About() {
  return (
    <>
      <h2 className="page-title">About KG RAG Demo</h2>
      <p className="page-subtitle">
        Unstructured biomedical text → knowledge graph → citation-grounded Q&A.
      </p>

      <section className="about-section">
        <h2>Pipeline</h2>
        <ol style={{ color: "var(--muted)", paddingLeft: "1.25rem" }}>
          <li>Seed documents in <code>data/documents/</code></li>
          <li>Chunk text and extract entities with rule-based patterns</li>
          <li>Store <code>Document</code>, <code>Chunk</code>, and entity nodes in Neo4j</li>
          <li>Embed chunks with sentence-transformers for vector retrieval</li>
          <li>Answer questions via RAG (retrieval + optional Ollama LLM)</li>
        </ol>
      </section>

      <section className="about-section">
        <h2>Graph schema</h2>
        <ul>
          <li>
            <strong>Nodes:</strong> Document, Chunk, Gene, Disease, Drug
          </li>
          <li>
            <strong>Edges:</strong> FROM_DOCUMENT, MENTIONS, ASSOCIATED_WITH, TREATS
          </li>
        </ul>
      </section>

      <section className="about-section">
        <h2>Limitations (MVP)</h2>
        <ul>
          <li>Synthetic corpus only — not clinical-grade</li>
          <li>Rule-based extraction; no fine-tuned NER</li>
          <li>LLM answers require Ollama locally (falls back to retrieval-only summary)</li>
          <li>No upload UI — ingest via API or seed scripts</li>
        </ul>
      </section>

      <section className="about-section">
        <h2>Stack &amp; sibling project</h2>
        <p>
          Neo4j · FastAPI · React + TypeScript · sentence-transformers. Pairs with{" "}
          <a href="https://github.com/LordKay-sudo/bioinsight-graph" target="_blank" rel="noreferrer">
            BioInsight Graph
          </a>{" "}
          (structured disease–target data). See{" "}
          <a href="/docs" target="_blank" rel="noreferrer">
            OpenAPI
          </a>{" "}
          for API reference.
        </p>
      </section>
    </>
  );
}
