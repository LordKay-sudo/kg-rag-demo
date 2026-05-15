import { NavLink } from "react-router-dom";

export default function Layout({ children }: { children: React.ReactNode }) {
  return (
    <div className="app-shell">
      <header className="app-header">
        <div className="app-header-inner">
          <NavLink to="/" className="brand">
            <div className="brand-icon">KG</div>
            <div>
              <h1>KG RAG Demo</h1>
              <p>Citation-grounded knowledge graph Q&A</p>
            </div>
          </NavLink>
          <nav className="nav-links">
            <NavLink to="/" end>
              Ask
            </NavLink>
            <NavLink to="/corpus">Corpus</NavLink>
            <NavLink to="/graph/BRCA1">Graph</NavLink>
            <NavLink to="/about">About</NavLink>
          </nav>
        </div>
      </header>
      <main className="app-main">{children}</main>
      <footer className="app-footer">
        <p>
          Pair with{" "}
          <a href="https://github.com/LordKay-sudo/bioinsight-graph" target="_blank" rel="noreferrer">
            BioInsight Graph
          </a>
          {" · "}
          <a href="/docs" target="_blank" rel="noreferrer">
            OpenAPI
          </a>
        </p>
      </footer>
    </div>
  );
}
