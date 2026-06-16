from __future__ import annotations

import re
from dataclasses import dataclass

from app.ingest.schema import (
    DISEASE_PHRASES,
    DRUG_CONFIDENCE,
    DRUG_DISEASE_RELATION_CONFIDENCE,
    DRUG_NAMES,
    GENE_ALLOWLIST,
    GENE_CONFIDENCE,
    GENE_DISEASE_RELATION_CONFIDENCE,
    DISEASE_CONFIDENCE,
)
from app.rag.query_expand import expand_question

# Bump when extraction rules change so provenance on MENTIONS edges is auditable (R7).
EXTRACTOR_VERSION = "rule-v1"

GENE_PATTERN = re.compile(r"\b([A-Z][A-Z0-9]{1,9})\b")


@dataclass
class ExtractedEntity:
    type: str
    id: str
    mention: str
    confidence: float = 1.0


@dataclass
class ExtractedRelation:
    source_type: str
    source_id: str
    target_type: str
    target_id: str
    relation: str
    confidence: float


def extract_entities(text: str) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
    """Schema-constrained extraction — see docs/EXTRACTION_SCHEMA.md."""
    text = expand_question(text)
    entities: list[ExtractedEntity] = []
    seen: set[tuple[str, str]] = set()

    for match in GENE_PATTERN.finditer(text):
        symbol = match.group(1)
        if symbol in GENE_ALLOWLIST:
            key = ("Gene", symbol)
            if key not in seen:
                seen.add(key)
                entities.append(
                    ExtractedEntity(type="Gene", id=symbol, mention=symbol, confidence=GENE_CONFIDENCE)
                )

    lower = text.lower()
    for phrase, disease_id in DISEASE_PHRASES.items():
        if phrase in lower:
            key = ("Disease", disease_id)
            if key not in seen:
                seen.add(key)
                entities.append(
                    ExtractedEntity(
                        type="Disease", id=disease_id, mention=phrase, confidence=DISEASE_CONFIDENCE
                    )
                )

    for drug_name, drug_id in DRUG_NAMES.items():
        if drug_name in lower:
            key = ("Drug", drug_id)
            if key not in seen:
                seen.add(key)
                entities.append(
                    ExtractedEntity(type="Drug", id=drug_id, mention=drug_name, confidence=DRUG_CONFIDENCE)
                )

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
                    confidence=GENE_DISEASE_RELATION_CONFIDENCE,
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
                    confidence=DRUG_DISEASE_RELATION_CONFIDENCE,
                )
            )

    return entities, relations
