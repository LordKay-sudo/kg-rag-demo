"""Register seed documents in Neo4j (metadata only; run ingest via API)."""
from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

from neo4j import GraphDatabase

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "api"))

from app.config import settings  # noqa: E402

INIT = (ROOT / "scripts" / "neo4j" / "init.cypher").read_text(encoding="utf-8")
DOCS_DIR = ROOT / "data" / "documents"


def main() -> None:
    driver = GraphDatabase.driver(
        settings.neo4j_uri, auth=(settings.neo4j_user, settings.neo4j_password)
    )
    try:
        driver.verify_connectivity()
        with driver.session() as session:
            for stmt in INIT.strip().split(";"):
                if stmt.strip():
                    session.run(stmt.strip())

            for path in sorted(DOCS_DIR.glob("*.txt")):
                doc_id = path.stem
                title = path.read_text(encoding="utf-8").splitlines()[0].replace("Title: ", "")
                session.run(
                    """
                    MERGE (d:Document {id: $id})
                    SET d.title = $title,
                        d.source = $source,
                        d.ingested_at = null,
                        d.status = 'pending'
                    """,
                    id=doc_id,
                    title=title,
                    source=str(path.name),
                )
                print(f"Registered {doc_id}: {title}")

        print(f"\nRegistered {len(list(DOCS_DIR.glob('*.txt')))} documents.")
        print("Ingest via: POST http://localhost:8000/api/v1/ingest/{document_id}")
    finally:
        driver.close()


if __name__ == "__main__":
    main()
