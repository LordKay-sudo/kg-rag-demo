"""Europe PMC open-access abstract fetch + document formatting (roadmap R13)."""
from __future__ import annotations

import json
import re
import textwrap
from pathlib import Path
from typing import Any

import httpx

EUROPE_PMC_SEARCH = "https://www.ebi.ac.uk/europepmc/webservices/rest/search"
DEFAULT_GENES = [
    "BRCA1", "BRCA2", "TP53", "EGFR", "BRAF", "KRAS", "CFTR", "APOE",
    "PTEN", "DMD", "PIK3CA", "ESR1",
]

SOURCE_LINE = "Europe PMC open access abstract"
LICENSE_NOTE = "Open-access full text; licence varies by publisher (often CC BY). See manifest."


def _clean_abstract(text: str) -> str:
    if not text:
        return ""
    # Strip HTML/XML tags occasionally present in Europe PMC abstracts.
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def format_epmc_document(
    *,
    title: str,
    abstract: str,
    pmid: str,
    doi: str | None = None,
    license_note: str | None = None,
) -> str:
    """Build a corpus .txt file with metadata header + abstract body."""
    lines = [
        f"Title: {title.strip()}",
        f"Source: {SOURCE_LINE}",
        f"PMID: {pmid}",
    ]
    if doi:
        lines.append(f"DOI: {doi}")
    lines.append(f"URL: https://europepmc.org/article/MED/{pmid}")
    if license_note:
        lines.append(f"License: {license_note}")
    body = _clean_abstract(abstract)
    return "\n".join(lines) + f"\n\n{body}\n"


def search_open_access_abstracts(
    gene: str,
    *,
    page_size: int = 25,
    cursor_mark: str = "*",
    client: httpx.Client | None = None,
) -> tuple[list[dict[str, Any]], str | None]:
    """Return OA Europe PMC hits with abstracts for a gene symbol."""
    query = f"{gene} AND OPEN_ACCESS:Y AND HAS_ABSTRACT:Y"
    params = {
        "query": query,
        "format": "json",
        "resultType": "core",
        "pageSize": page_size,
        "cursorMark": cursor_mark,
    }
    own = client is None
    if own:
        client = httpx.Client(timeout=30.0)
    try:
        r = client.get(EUROPE_PMC_SEARCH, params=params)
        r.raise_for_status()
        data = r.json()
    finally:
        if own:
            client.close()

    results = data.get("resultList", {}).get("result") or []
    next_cursor = data.get("nextCursorMark")
    hits: list[dict[str, Any]] = []
    seen_pmids: set[str] = set()
    for row in results:
        pmid = str(row.get("pmid") or row.get("id") or "").strip()
        abstract = _clean_abstract(row.get("abstractText") or "")
        if not pmid or not abstract or pmid in seen_pmids:
            continue
        seen_pmids.add(pmid)
        hits.append(
            {
                "pmid": pmid,
                "title": (row.get("title") or f"PMID {pmid}").strip(),
                "abstract": abstract,
                "doi": (row.get("doi") or "").strip() or None,
                "gene_query": gene,
                "is_open_access": row.get("isOpenAccess") == "Y",
                "source": row.get("source") or "MED",
            }
        )
    return hits, next_cursor


def download_corpus(
    *,
    genes: list[str] | None = None,
    max_per_gene: int = 6,
    max_total: int = 60,
    output_dir: Path,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Download OA abstracts and write corpus files + manifest JSON."""
    genes = genes or DEFAULT_GENES
    output_dir.mkdir(parents=True, exist_ok=True)
    manifest_path = manifest_path or (output_dir / "manifest" / "epmc_manifest.json")
    manifest_path.parent.mkdir(parents=True, exist_ok=True)

    seen_pmids: set[str] = set()
    entries: list[dict[str, Any]] = []
    files_written = 0

    with httpx.Client(timeout=30.0) as client:
        for gene in genes:
            if files_written >= max_total:
                break
            per_gene = 0
            cursor = "*"
            while per_gene < max_per_gene and files_written < max_total:
                hits, next_cursor = search_open_access_abstracts(
                    gene, cursor_mark=cursor, client=client
                )
                if not hits:
                    break
                for hit in hits:
                    if hit["pmid"] in seen_pmids:
                        continue
                    seen_pmids.add(hit["pmid"])
                    doc_id = f"epmc-{hit['pmid']}"
                    path = output_dir / f"{doc_id}.txt"
                    path.write_text(
                        format_epmc_document(
                            title=hit["title"],
                            abstract=hit["abstract"],
                            pmid=hit["pmid"],
                            doi=hit["doi"],
                            license_note=LICENSE_NOTE,
                        ),
                        encoding="utf-8",
                    )
                    entries.append({**hit, "document_id": doc_id, "file": path.name})
                    files_written += 1
                    per_gene += 1
                    if per_gene >= max_per_gene or files_written >= max_total:
                        break
                if not next_cursor or next_cursor == cursor:
                    break
                cursor = next_cursor

    manifest = {
        "source": "Europe PMC REST API",
        "api_url": EUROPE_PMC_SEARCH,
        "license_summary": (
            "Open-access articles only (OPEN_ACCESS:Y). Individual article licences "
            "are set by publishers; many are CC BY. Verify on Europe PMC before reuse."
        ),
        "gene_queries": genes,
        "document_count": len(entries),
        "documents": entries,
    }
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest
