from fastapi import APIRouter, HTTPException, Query

from app.db import get_session
from app.models.schemas import ExploreResponse, SubgraphLink, SubgraphNode

router = APIRouter(prefix="/graph", tags=["graph"])


def _display_name(label: str, row: dict) -> str:
    if label == "Gene":
        return row.get("symbol") or row.get("name") or row["id"]
    if label == "Document":
        return row.get("title") or row["id"]
    if label in ("Disease", "Drug"):
        return row.get("name") or row["id"]
    return row["id"]


@router.get("/explore", response_model=ExploreResponse)
def explore(entity_id: str = Query(..., description="Entity id (Gene, Disease, Drug, etc.)")) -> ExploreResponse:
    with get_session() as session:
        center = session.run(
            """
            MATCH (n) WHERE n.id = $id
            RETURN labels(n)[0] AS label, n.id AS id, n.name AS name,
                   n.symbol AS symbol, n.title AS title
            LIMIT 1
            """,
            id=entity_id,
        ).single()

        if not center:
            raise HTTPException(status_code=404, detail="Entity not found")

        nodes_result = session.run(
            """
            MATCH (center) WHERE center.id = $id
            OPTIONAL MATCH (center)-[r]-(neighbor)
            WHERE neighbor IS NOT NULL
            WITH collect(DISTINCT center) + collect(DISTINCT neighbor) AS raw
            UNWIND raw AS n
            WITH DISTINCT n
            RETURN labels(n)[0] AS label, n.id AS id, n.name AS name,
                   n.symbol AS symbol, n.title AS title
            """,
            id=entity_id,
        ).data()

        links_result = session.run(
            """
            MATCH (center) WHERE center.id = $id
            MATCH (center)-[r]-(neighbor)
            RETURN center.id AS source, neighbor.id AS target, type(r) AS type
            """,
            id=entity_id,
        ).data()

    nodes = [
        SubgraphNode(
            id=r["id"],
            label=r["label"],
            name=_display_name(r["label"], r),
        )
        for r in nodes_result
        if r["id"]
    ]
    node_ids = {n.id for n in nodes}
    links = [
        SubgraphLink(source=r["source"], target=r["target"], type=r["type"])
        for r in links_result
        if r["source"] and r["target"] and r["type"] and r["source"] in node_ids and r["target"] in node_ids
    ]
    seen = set()
    unique_links: list[SubgraphLink] = []
    for link in links:
        key = (link.source, link.target, link.type)
        rev = (link.target, link.source, link.type)
        if key in seen or rev in seen:
            continue
        seen.add(key)
        unique_links.append(link)

    return ExploreResponse(entity_id=entity_id, nodes=nodes, links=unique_links)
