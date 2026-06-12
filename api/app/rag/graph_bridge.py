"""Optional BioInsight graph evidence check for conditional retrieval (roadmap R10)."""
from __future__ import annotations

import httpx

from app.config import settings
from app.identifiers import resolve_gene_id


def graph_evidence_is_weak(gene_id: str, *, min_association_score: float = 0.35) -> bool:
    """Return True when BioInsight reports sparse/weak disease evidence for a gene.

    If BioInsight is unreachable or ``bioinsight_api_url`` is unset, returns False
    (do not widen retrieval on network failure).
    """
    base = (settings.bioinsight_api_url or "").strip().rstrip("/")
    if not base:
        return False

    ensg = resolve_gene_id(gene_id) or gene_id
    if not ensg.startswith("ENSG"):
        # Try symbol lookup path — BioInsight accepts ENSG in path; resolve first.
        resolved = resolve_gene_id(gene_id.upper())
        if resolved:
            ensg = resolved
        else:
            return False

    url = f"{base}/api/v1/genes/{ensg}/diseases"
    try:
        with httpx.Client(timeout=8.0) as client:
            r = client.get(url)
            if r.status_code == 404:
                return True
            r.raise_for_status()
            body = r.json()
    except Exception:
        return False

    diseases = body.get("diseases") or []
    if not diseases:
        return True
    top = max(float(d.get("score") or 0.0) for d in diseases)
    return top < min_association_score
