"""Ontology-guided extraction schema S=(E, R, Φ) for kg-rag-demo (roadmap R16).

Human-readable spec: docs/EXTRACTION_SCHEMA.md
BioInsight structured graph schema: bioinsight-graph/docs/ONTOLOGY_SCHEMA.md
"""
from __future__ import annotations

# --- Entity types (E) -------------------------------------------------------

ENTITY_TYPES: tuple[str, ...] = ("Gene", "Disease", "Drug")

# --- Relation types (R) with domain → range (Φ) -----------------------------

RELATION_TYPES: dict[str, tuple[str, str]] = {
    "ASSOCIATED_WITH": ("Gene", "Disease"),
    "TREATS": ("Drug", "Disease"),
}

# --- Allowlists (ontology-guided extraction) --------------------------------

GENE_ALLOWLIST: frozenset[str] = frozenset(
    {
        "BRCA1", "BRCA2", "TP53", "EGFR", "BRAF", "KRAS", "CFTR", "APOE", "APP",
        "PSEN1", "DMD", "PTEN", "NRAS", "HRAS", "PIK3CA", "MYC", "RB1", "ESR1",
    }
)

DISEASE_PHRASES: dict[str, str] = {
    "breast cancer": "breast_cancer",
    "ovarian cancer": "ovarian_cancer",
    "lung carcinoma": "lung_carcinoma",
    "lung cancer": "lung_cancer",
    "melanoma": "melanoma",
    "cystic fibrosis": "cystic_fibrosis",
    "alzheimer disease": "alzheimer_disease",
    "duchenne muscular dystrophy": "duchenne_muscular_dystrophy",
    "prostate cancer": "prostate_cancer",
    "colorectal cancer": "colorectal_cancer",
}

DRUG_NAMES: dict[str, str] = {
    "olaparib": "olaparib",
    "erlotinib": "erlotinib",
    "gefitinib": "gefitinib",
    "vemurafenib": "vemurafenib",
    "dabrafenib": "dabrafenib",
    "trametinib": "trametinib",
    "ivacaftor": "ivacaftor",
    "tezacaftor": "tezacaftor",
}

# --- Per-kind confidence defaults (rule-based extractor) ----------------------

GENE_CONFIDENCE = 0.9
DISEASE_CONFIDENCE = 0.85
DRUG_CONFIDENCE = 0.8
GENE_DISEASE_RELATION_CONFIDENCE = 0.7
DRUG_DISEASE_RELATION_CONFIDENCE = 0.6


def relation_allowed(relation: str, source_type: str, target_type: str) -> bool:
    """Return True when relation matches schema domain/range."""
    domain_range = RELATION_TYPES.get(relation)
    if not domain_range:
        return False
    domain, range_ = domain_range
    return source_type == domain and target_type == range_
