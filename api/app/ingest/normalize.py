"""Post-extraction normalization before Neo4j write (roadmap R17).

ML6-style uniformisation: canonical ids, alias merge, dedupe, schema validation.
See docs/EXTRACTION_SCHEMA.md § Normalization pipeline.
"""
from __future__ import annotations

from app.ingest.extractor import ExtractedEntity, ExtractedRelation
from app.ingest.schema import relation_allowed
from app.rag.query_expand import normalize_gene_token

NORMALIZER_VERSION = "norm-v1"


def canonical_entity_id(entity_type: str, entity_id: str) -> str:
    """Map extractor ids to canonical graph keys."""
    if entity_type == "Gene":
        canonical = normalize_gene_token(entity_id)
        return canonical if canonical else entity_id.upper()
    if entity_type in ("Disease", "Drug"):
        return entity_id.lower().strip()
    return entity_id


def normalize_entities(entities: list[ExtractedEntity]) -> list[ExtractedEntity]:
    """Dedupe entities by canonical (type, id); keep highest confidence."""
    best: dict[tuple[str, str], ExtractedEntity] = {}
    for ent in entities:
        if ent.type not in ("Gene", "Disease", "Drug"):
            continue
        canonical_id = canonical_entity_id(ent.type, ent.id)
        key = (ent.type, canonical_id)
        candidate = ExtractedEntity(
            type=ent.type,
            id=canonical_id,
            mention=ent.mention,
            confidence=ent.confidence,
        )
        existing = best.get(key)
        if existing is None or candidate.confidence > existing.confidence:
            best[key] = candidate
    return list(best.values())


def normalize_relations(
    entities: list[ExtractedEntity],
    relations: list[ExtractedRelation],
) -> list[ExtractedRelation]:
    """Canonicalize relation endpoints, validate domain/range, dedupe."""
    entity_keys = {(e.type, e.id) for e in entities}
    best: dict[tuple[str, str, str, str, str], ExtractedRelation] = {}

    for rel in relations:
        source_id = canonical_entity_id(rel.source_type, rel.source_id)
        target_id = canonical_entity_id(rel.target_type, rel.target_id)
        if (rel.source_type, source_id) not in entity_keys:
            continue
        if (rel.target_type, target_id) not in entity_keys:
            continue
        if not relation_allowed(rel.relation, rel.source_type, rel.target_type):
            continue

        key = (rel.source_type, source_id, rel.relation, rel.target_type, target_id)
        candidate = ExtractedRelation(
            source_type=rel.source_type,
            source_id=source_id,
            target_type=rel.target_type,
            target_id=target_id,
            relation=rel.relation,
            confidence=rel.confidence,
        )
        existing = best.get(key)
        if existing is None or candidate.confidence > existing.confidence:
            best[key] = candidate

    return list(best.values())


def normalize_extraction(
    entities: list[ExtractedEntity],
    relations: list[ExtractedRelation],
) -> tuple[list[ExtractedEntity], list[ExtractedRelation]]:
    """Run full normalization pipeline for one chunk."""
    normalized_entities = normalize_entities(entities)
    normalized_relations = normalize_relations(normalized_entities, relations)
    return normalized_entities, normalized_relations
