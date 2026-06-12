"""Resolve clickable literature references for citations (roadmap R2).

A document may carry optional source metadata: ``pmid``, ``doi``, ``url``. This
module turns whatever is present into a single canonical ``reference_url`` and a
short human label, preferring the most specific identifier available:

    url  >  doi (https://doi.org/...)  >  pmid (Europe PMC)  >  title search

The title-search fallback never fabricates a specific article id; it links to a
Europe PMC search so reviewers can locate the source.
"""
from __future__ import annotations

import re
from urllib.parse import quote_plus

EUROPE_PMC_ARTICLE = "https://europepmc.org/article/MED/{pmid}"
EUROPE_PMC_SEARCH = "https://europepmc.org/search?query={query}"
DOI_BASE = "https://doi.org/{doi}"

_PMID_RE = re.compile(r"^\d{1,9}$")
_DOI_RE = re.compile(r"^10\.\d{4,9}/\S+$")


def normalize_pmid(pmid: str | None) -> str | None:
    if not pmid:
        return None
    value = pmid.strip().removeprefix("PMID:").strip()
    return value if _PMID_RE.match(value) else None


def normalize_doi(doi: str | None) -> str | None:
    if not doi:
        return None
    value = doi.strip().removeprefix("doi:").removeprefix("DOI:").strip()
    value = value.removeprefix("https://doi.org/").removeprefix("http://doi.org/")
    return value if _DOI_RE.match(value) else None


def resolve_reference_url(
    *,
    url: str | None = None,
    doi: str | None = None,
    pmid: str | None = None,
    title: str | None = None,
) -> str | None:
    """Return the best clickable reference URL from available metadata."""
    if url and url.strip().startswith("http"):
        return url.strip()

    norm_doi = normalize_doi(doi)
    if norm_doi:
        return DOI_BASE.format(doi=norm_doi)

    norm_pmid = normalize_pmid(pmid)
    if norm_pmid:
        return EUROPE_PMC_ARTICLE.format(pmid=norm_pmid)

    if title and title.strip():
        return EUROPE_PMC_SEARCH.format(query=quote_plus(title.strip()))

    return None
