from app.ingest.extractor import ExtractedEntity, ExtractedRelation
from app.ingest.normalize import (
    NORMALIZER_VERSION,
    canonical_entity_id,
    normalize_entities,
    normalize_extraction,
    normalize_relations,
)


def test_canonical_entity_id_maps_gene_alias():
    assert canonical_entity_id("Gene", "BRCA-1") == "BRCA1"
    assert canonical_entity_id("Disease", "Breast_Cancer") == "breast_cancer"
    assert canonical_entity_id("Drug", "Olaparib") == "olaparib"


def test_normalize_entities_dedupes_gene_aliases():
    entities = [
        ExtractedEntity(type="Gene", id="BRCA1", mention="BRCA1", confidence=0.9),
        ExtractedEntity(type="Gene", id="BRCA-1", mention="BRCA-1", confidence=0.8),
    ]
    out = normalize_entities(entities)
    assert len(out) == 1
    assert out[0].id == "BRCA1"
    assert out[0].confidence == 0.9


def test_normalize_relations_validates_domain_range():
    entities = [
        ExtractedEntity(type="Gene", id="BRCA1", mention="BRCA1", confidence=0.9),
        ExtractedEntity(type="Disease", id="breast_cancer", mention="breast cancer", confidence=0.85),
    ]
    relations = [
        ExtractedRelation(
            source_type="Gene",
            source_id="BRCA-1",
            target_type="Disease",
            target_id="breast_cancer",
            relation="ASSOCIATED_WITH",
            confidence=0.7,
        ),
        ExtractedRelation(
            source_type="Disease",
            source_id="breast_cancer",
            target_type="Gene",
            target_id="BRCA1",
            relation="ASSOCIATED_WITH",
            confidence=0.5,
        ),
    ]
    out = normalize_relations(entities, relations)
    assert len(out) == 1
    assert out[0].source_id == "BRCA1"
    assert out[0].target_id == "breast_cancer"


def test_normalize_extraction_dedupes_relations():
    entities = [
        ExtractedEntity(type="Gene", id="BRCA1", mention="BRCA1", confidence=0.9),
        ExtractedEntity(type="Disease", id="breast_cancer", mention="breast cancer", confidence=0.85),
    ]
    relations = [
        ExtractedRelation(
            source_type="Gene",
            source_id="BRCA1",
            target_type="Disease",
            target_id="breast_cancer",
            relation="ASSOCIATED_WITH",
            confidence=0.7,
        ),
        ExtractedRelation(
            source_type="Gene",
            source_id="BRCA-1",
            target_type="Disease",
            target_id="breast_cancer",
            relation="ASSOCIATED_WITH",
            confidence=0.6,
        ),
    ]
    entities_out, relations_out = normalize_extraction(entities, relations)
    assert len(entities_out) == 2
    assert len(relations_out) == 1
    assert relations_out[0].confidence == 0.7


def test_normalizer_version_is_set():
    assert NORMALIZER_VERSION.startswith("norm-")
