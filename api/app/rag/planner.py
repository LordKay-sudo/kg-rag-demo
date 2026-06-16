"""Decompose questions into sub-queries before retrieval (roadmap R9)."""
from __future__ import annotations

from app.identifiers import resolve_disease_id, resolve_gene_id
from app.ingest.schema import DISEASE_PHRASES, DRUG_NAMES
from app.rag.graph_bridge import graph_evidence_is_weak
from app.rag.query_expand import expand_question, gene_symbols_in_text


def _diseases_in_text(text: str) -> list[tuple[str, str]]:
    """Return (slug, phrase) disease hits in lowercased text."""
    lower = text.lower()
    hits: list[tuple[str, str]] = []
    seen: set[str] = set()
    for phrase, slug in sorted(DISEASE_PHRASES.items(), key=lambda x: -len(x[0])):
        if phrase in lower and slug not in seen:
            seen.add(slug)
            hits.append((slug, phrase))
    return hits


def _drugs_in_text(text: str) -> list[str]:
    lower = text.lower()
    return [name for name in DRUG_NAMES if name in lower]


def plan_question(
    question: str,
    *,
    gene_id: str | None = None,
    disease_id: str | None = None,
) -> dict:
    """Build a JSON plan: intent, sub-queries, suggested entity ids, widen hint."""
    expanded = expand_question(question)
    genes = gene_symbols_in_text(expanded)
    diseases = _diseases_in_text(expanded)
    drugs = _drugs_in_text(expanded)

    if gene_id:
        sym = gene_id.upper() if not gene_id.startswith("ENSG") else None
        if sym and sym not in genes:
            genes.insert(0, sym)
        elif gene_id.startswith("ENSG"):
            for g, ens in _gene_from_ensg(gene_id):
                if g not in genes:
                    genes.insert(0, g)

    steps: list[dict] = []
    for symbol in genes:
        steps.append(
            {
                "sub_query": f"What does the literature say about {symbol}?",
                "entity_type": "Gene",
                "entity_id": symbol,
                "ontology_id": resolve_gene_id(symbol),
            }
        )
    for slug, phrase in diseases:
        steps.append(
            {
                "sub_query": f"Which genes or drugs are linked to {phrase}?",
                "entity_type": "Disease",
                "entity_id": slug,
                "ontology_id": resolve_disease_id(slug),
            }
        )
    for drug in drugs:
        steps.append(
            {
                "sub_query": f"What diseases or targets involve {drug}?",
                "entity_type": "Drug",
                "entity_id": drug,
                "ontology_id": None,
            }
        )

    if not steps:
        steps.append(
            {
                "sub_query": question.strip(),
                "entity_type": None,
                "entity_id": None,
                "ontology_id": None,
            }
        )

    if genes and diseases:
        intent = "gene_disease"
    elif genes:
        intent = "gene"
    elif diseases:
        intent = "disease"
    elif drugs:
        intent = "drug"
    else:
        intent = "general"

    suggested_gene = gene_id or (genes[0] if genes else None)
    suggested_disease = disease_id or (diseases[0][0] if diseases else None)

    widen = False
    check_gene = suggested_gene or (genes[0] if genes else None)
    if check_gene:
        widen = graph_evidence_is_weak(check_gene)

    return {
        "question": question,
        "expanded_question": expanded,
        "intent": intent,
        "steps": steps,
        "suggested_gene_id": suggested_gene,
        "suggested_disease_id": suggested_disease,
        "widen_retrieval": widen,
    }


def _gene_from_ensg(ensg: str) -> list[tuple[str, str]]:
    from app.identifiers import GENE_TO_ENSG

    return [(sym, ensg) for sym, eid in GENE_TO_ENSG.items() if eid == ensg]
