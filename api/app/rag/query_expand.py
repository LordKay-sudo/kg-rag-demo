"""Query expansion and gene synonym normalization (roadmap R11)."""
from __future__ import annotations

import re

from app.identifiers import resolve_gene_id

# Common hyphenated / alias forms -> canonical HGNC symbol.
GENE_ALIASES: dict[str, str] = {
    "BRCA-1": "BRCA1",
    "BRCA-2": "BRCA2",
    "TP-53": "TP53",
    "P53": "TP53",
    "CFTR-G551D": "CFTR",  # variant mention -> gene
}

GENE_TOKEN = re.compile(r"\b([A-Za-z][A-Za-z0-9-]{0,14})\b")


def normalize_gene_token(token: str) -> str | None:
    """Map a token (BRCA-1, brca1) to a canonical symbol if known."""
    upper = token.upper()
    if upper in GENE_ALIASES:
        return GENE_ALIASES[upper]
    compact = upper.replace("-", "")
    if compact in GENE_ALIASES:
        return GENE_ALIASES[compact]
    # Allowlist check via resolve_gene_id keys — import from extractor would cycle;
    # resolve_gene_id only knows canonical symbols.
    if resolve_gene_id(compact):
        return compact
    if resolve_gene_id(upper):
        return upper
    return None


def expand_question(question: str) -> str:
    """Return question text with gene aliases replaced by canonical symbols."""

    def repl(match: re.Match[str]) -> str:
        token = match.group(1)
        canonical = normalize_gene_token(token)
        return canonical if canonical else token

    return GENE_TOKEN.sub(repl, question)


def gene_symbols_in_text(text: str) -> list[str]:
    """Detect canonical gene symbols present in text (after alias normalization)."""
    expanded = expand_question(text)
    seen: set[str] = set()
    symbols: list[str] = []
    for match in GENE_TOKEN.finditer(expanded):
        canonical = normalize_gene_token(match.group(1))
        if canonical and canonical not in seen:
            seen.add(canonical)
            symbols.append(canonical)
    return symbols
