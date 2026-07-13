"""ClinicalTrials.gov registry summaries → corpus documents for GapForge RAG."""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

import httpx

CT_API = "https://clinicaltrials.gov/api/v2/studies"
SOURCE_LINE = "ClinicalTrials.gov registry summary"


def _clean(text: str) -> str:
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_ct_document(
    *,
    nct_id: str,
    title: str,
    summary: str,
    phase: str | None = None,
    status: str | None = None,
    conditions: list[str] | None = None,
) -> str:
    lines = [
        f"Title: {title.strip()}",
        f"Source: {SOURCE_LINE}",
        f"NCT: {nct_id}",
        f"URL: https://clinicaltrials.gov/study/{nct_id}",
    ]
    if phase:
        lines.append(f"Phase: {phase}")
    if status:
        lines.append(f"Status: {status}")
    if conditions:
        lines.append(f"Conditions: {', '.join(conditions)}")
    body = _clean(summary) or f"ClinicalTrials.gov study {nct_id}."
    return "\n".join(lines) + f"\n\n{body}\n"


def fetch_study(nct_id: str, *, client: httpx.Client | None = None) -> dict[str, Any] | None:
    """Fetch a single study by NCT id via ClinicalTrials.gov API v2."""
    own = client is None
    if own:
        client = httpx.Client(timeout=30.0)
    try:
        r = client.get(f"{CT_API}/{nct_id}", params={"format": "json"})
        if r.status_code == 404:
            return None
        r.raise_for_status()
        return r.json()
    finally:
        if own:
            client.close()


def study_to_fields(payload: dict[str, Any]) -> dict[str, Any]:
    proto = payload.get("protocolSection") or {}
    ident = proto.get("identificationModule") or {}
    status_mod = proto.get("statusModule") or {}
    design = proto.get("designModule") or {}
    cond = proto.get("conditionsModule") or {}
    desc = proto.get("descriptionModule") or {}
    phases = design.get("phases") or []
    phase = ", ".join(phases) if phases else None
    return {
        "nct_id": ident.get("nctId") or "",
        "title": ident.get("officialTitle") or ident.get("briefTitle") or "Untitled study",
        "summary": desc.get("briefSummary") or desc.get("detailedDescription") or "",
        "phase": phase,
        "status": (status_mod.get("overallStatus") or ""),
        "conditions": cond.get("conditions") or [],
    }


def download_studies(
    nct_ids: list[str],
    out_dir: Path,
    *,
    client: httpx.Client | None = None,
) -> list[Path]:
    """Write one .txt document per NCT id. Returns written paths."""
    out_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    own = client is None
    if own:
        client = httpx.Client(timeout=30.0)
    try:
        for nct in nct_ids:
            nct = nct.strip().upper()
            if not nct:
                continue
            payload = fetch_study(nct, client=client)
            if not payload:
                # Offline / missing: write curated stub so pipeline still runs
                path = out_dir / f"ctgov-{nct.lower()}.txt"
                path.write_text(
                    format_ct_document(
                        nct_id=nct,
                        title=f"ClinicalTrials.gov {nct}",
                        summary=(
                            f"Registry stub for {nct}. Fetch failed or study missing; "
                            "replace by re-running download when network is available."
                        ),
                    ),
                    encoding="utf-8",
                )
                written.append(path)
                continue
            fields = study_to_fields(payload)
            path = out_dir / f"ctgov-{nct.lower()}.txt"
            path.write_text(
                format_ct_document(
                    nct_id=fields["nct_id"] or nct,
                    title=fields["title"],
                    summary=fields["summary"],
                    phase=fields["phase"],
                    status=fields["status"],
                    conditions=fields["conditions"],
                ),
                encoding="utf-8",
            )
            written.append(path)
    finally:
        if own:
            client.close()
    return written


def write_manifest(paths: list[Path], manifest_path: Path, *, note: str) -> None:
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    entries = [{"document_id": p.stem, "path": str(p.name)} for p in paths]
    manifest_path.write_text(
        json.dumps({"note": note, "documents": entries}, indent=2),
        encoding="utf-8",
    )
