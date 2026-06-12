"""Shared ontology identifiers with BioInsight Graph (roadmap R5).

kg-rag extracts gene/disease symbols from free text. To tell *one platform story*
with [bioinsight-graph](https://github.com/LordKay-sudo/bioinsight-graph), those
symbols resolve to the same stable public identifiers BioInsight uses as graph
keys: Ensembl ``ENSG`` ids for genes and EFO/MONDO ids for diseases.

This is a curated lookup table for the demo corpus, not a full ontology service.
Symbols outside the table resolve to ``None`` (still stored by symbol).
"""
from __future__ import annotations

# Gene symbol -> Ensembl stable gene id (canonical public IDs, GRCh38).
GENE_TO_ENSG: dict[str, str] = {
    "BRCA1": "ENSG00000012048",
    "BRCA2": "ENSG00000139618",
    "TP53": "ENSG00000141510",
    "EGFR": "ENSG00000146648",
    "BRAF": "ENSG00000157764",
    "KRAS": "ENSG00000133703",
    "CFTR": "ENSG00000001626",
    "APOE": "ENSG00000130203",
    "APP": "ENSG00000142192",
    "PSEN1": "ENSG00000080815",
    "DMD": "ENSG00000198947",
    "PTEN": "ENSG00000171862",
    "NRAS": "ENSG00000213281",
    "HRAS": "ENSG00000174775",
    "PIK3CA": "ENSG00000121879",
    "MYC": "ENSG00000136997",
    "RB1": "ENSG00000139687",
    "ESR1": "ENSG00000091831",
}

# Disease slug (extractor id) -> EFO / MONDO ontology id (Open Targets-aligned).
DISEASE_TO_ONTOLOGY: dict[str, str] = {
    "breast_cancer": "EFO_0000305",
    "ovarian_cancer": "EFO_0001075",
    "lung_carcinoma": "EFO_0001071",
    "lung_cancer": "MONDO_0008903",
    "melanoma": "EFO_0000756",
    "cystic_fibrosis": "MONDO_0009061",
    "alzheimer_disease": "MONDO_0004975",
    "duchenne_muscular_dystrophy": "MONDO_0010679",
    "prostate_cancer": "EFO_0001663",
    "colorectal_cancer": "EFO_0005842",
}


def resolve_gene_id(symbol: str) -> str | None:
    """Map a gene symbol to its Ensembl ENSG id, or None if unknown."""
    return GENE_TO_ENSG.get((symbol or "").upper())


def resolve_disease_id(slug: str) -> str | None:
    """Map a disease slug to its EFO/MONDO ontology id, or None if unknown."""
    return DISEASE_TO_ONTOLOGY.get((slug or "").lower())


def resolve_entity_id(entity_type: str, entity_id: str) -> str | None:
    """Resolve an extracted entity to its shared ontology id (BioInsight join key)."""
    if entity_type == "Gene":
        return resolve_gene_id(entity_id)
    if entity_type == "Disease":
        return resolve_disease_id(entity_id)
    return None
