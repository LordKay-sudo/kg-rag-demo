"""PeerLens quality-signal pre-filter for papers entering RAG ingest."""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class PeerLensFilterResult:
    identifier: str
    allowed: bool
    reasons: list[str]
    signals: list[dict[str, Any]]
    skipped: bool = False


def peerlens_base_url() -> str:
    return os.getenv("PEERLENS_API_URL", "http://localhost:8000").rstrip("/")


def analyze_identifier(
    identifier: str,
    *,
    base_url: str | None = None,
    client: httpx.Client | None = None,
    timeout: float = 20.0,
) -> dict[str, Any] | None:
    """POST /api/v1/papers/analyze — returns QualityReport dict or None on transport failure."""
    url = f"{(base_url or peerlens_base_url())}/api/v1/papers/analyze"
    own = client is None
    if own:
        client = httpx.Client(timeout=timeout)
    try:
        r = client.post(url, json={"identifier": identifier})
        if r.status_code >= 400:
            return None
        return r.json()
    except Exception:
        return None
    finally:
        if own:
            client.close()


def filter_paper(
    identifier: str,
    *,
    base_url: str | None = None,
    block_severities: frozenset[str] = frozenset({"concern"}),
    block_signal_ids: frozenset[str] = frozenset({"paper_retracted"}),
    fail_open: bool = True,
) -> PeerLensFilterResult:
    """
    Gate a DOI / arXiv id before RAG ingest.

    - Blocks if PeerLens returns severity in block_severities or signal id in block_signal_ids.
    - If PeerLens is unreachable and fail_open=True, allows with skipped=True.
    """
    report = analyze_identifier(identifier, base_url=base_url)
    if report is None:
        return PeerLensFilterResult(
            identifier=identifier,
            allowed=fail_open,
            reasons=["peerlens_unreachable" if fail_open else "peerlens_unreachable_blocked"],
            signals=[],
            skipped=True,
        )

    signals = report.get("signals") or []
    reasons: list[str] = []
    for s in signals:
        sid = s.get("id") or ""
        sev = (s.get("severity") or "").lower()
        if sid in block_signal_ids:
            reasons.append(f"blocked_signal:{sid}")
        if sev in block_severities:
            reasons.append(f"blocked_severity:{sev}:{sid}")

    allowed = len(reasons) == 0
    if allowed:
        reasons.append("passed")
    return PeerLensFilterResult(
        identifier=identifier,
        allowed=allowed,
        reasons=reasons,
        signals=signals,
        skipped=False,
    )
