"""Parse optional source metadata from a document header (roadmap R2).

Document files start with a small header of ``Key: value`` lines, followed by a
blank line and the body. ``Title`` is required; ``Source``, ``PMID``, ``DOI``, and
``URL`` are optional and power clickable citations.

    Title: BRCA1 and breast cancer risk
    Source: Synthetic demo abstract
    PMID: 20301425
    DOI: 10.1000/example

    BRCA1 mutations substantially increase ...
"""
from __future__ import annotations

from dataclasses import dataclass

_KNOWN_KEYS = {"title", "source", "pmid", "doi", "url"}


@dataclass
class DocumentMetadata:
    title: str
    body: str
    source: str | None = None
    pmid: str | None = None
    doi: str | None = None
    url: str | None = None


def parse_document(raw: str, *, fallback_title: str = "") -> DocumentMetadata:
    """Split a raw document into header metadata and body text."""
    lines = raw.splitlines()
    meta: dict[str, str] = {}
    body_start = 0

    for idx, line in enumerate(lines):
        stripped = line.strip()
        if stripped == "":
            body_start = idx + 1
            break
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            key = key.strip().lower()
            if key in _KNOWN_KEYS:
                meta[key] = value.strip()
                body_start = idx + 1
                continue
        # First non-metadata line ends the header.
        body_start = idx
        break

    body = "\n".join(lines[body_start:]).strip()
    if not body:
        # No header/body separation; treat the whole thing as body.
        body = raw.strip()

    title = meta.get("title") or fallback_title or "Untitled"
    return DocumentMetadata(
        title=title,
        body=body,
        source=meta.get("source"),
        pmid=meta.get("pmid"),
        doi=meta.get("doi"),
        url=meta.get("url"),
    )
