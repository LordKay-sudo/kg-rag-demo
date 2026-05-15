from __future__ import annotations

import re
from dataclasses import dataclass

GENE_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]{1,9})\b")

DISEASE_PHRASES = {
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

DRUG_NAMES = {
    "olaparib": "olaparib",
    "erlotinib": "erlotinib",
    "gefitinib": "gefitinib",
    "vemurafenib": "vemurafenib",
    "dabrafenib": "dabrafenib",
    "trametinib": "trametinib",
    "ivacaftor": "ivacaftor",
    "tezacaftor": "tezacaftor",
}

GENE_ALLOWLIST = {
    "BRCA1", "BRCA2", "TP53", "EGFR", "BRAF", "KRAS", "CFTR", "APOE", "APP",
    "PSEN1", "DMD", "PTEN", "NRAS", "HRAS", "PIK3CA", "MYC", "RB1", "ESR1",
}


@dataclass
class ExtractedEntity:
    type: str
    id: str
    mention: str


@dataclass
class ExtractedRelation:
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relation: str
    confidence: float


def extract_entities(text: str) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
    entities: list[ExtractedEntity] = []
    seen: set[tuple[str, str]] = set()

    for match in GENE_PATTERN.finditer(text):
        symbol = match.group(1)
        if symbol in GENE_ALLOWLIST:
            key = ("Gene", symbol)
            if key not in seen:
                seen.add(key)
                entities.append(ExtractedEntity(type="Gene", id=symbol, mention=symbol))

    lower = text.lower()
    for phrase, disease_id in DISEASE_PHRASES.items():
        if phrase in lower:
            key = ("Disease", disease_id)
            if key not in seen:
                seen.add(key)
                entities.append(ExtractedEntity(type="Disease", id=disease_id, mention=phrase))

    for drug_name, drug_id in DRUG_NAMES.items():
        if drug_name in lower:
            key = ("Drug", drug_id)
            if key not in seen:
                seen.add(key)
                entities.append(ExtractedEntity(type="Drug", id=drug_id, mention=drug_name))

    relations: list[ExtractedRelation] = []
    genes = [e for e in entities if e.type == "Gene"]
    diseases = [e for e in entities if e.type == "Disease"]
    drugs = [e for e in entities if e.type == "Drug"]

    for g in genes:
        for d in diseases:
            relations.append(
                ExtractedRelation(
                    source_type="Gene",
                    source_id=g.id,
                    target_type="Disease",
                    target_id=d.id,
                    relation="ASSOCIATED_WITH",
                    confidence=0.7,
                )
            )
    for drug in drugs:
        for d in diseases:
            relations.append(
                ExtractedRelation(
                    source_type="Drug",
                    source_id=drug.id,
                    target_type="Disease",
                    target_id=d.id,
                    relation="TREATS",
                    confidence=0.6,
                )
            )

    return entities, relations
