from app.ingest.extractor import EXTRACTOR_VERSION, extract_entities


def test_extracts_gene_and_disease():
    text = "BRCA1 mutations increase breast cancer risk."
    entities, relations = extract_entities(text)
    types = {e.type for e in entities}
    assert "Gene" in types
    assert "Disease" in types
    assert any(r.relation == "ASSOCIATED_WITH" for r in relations)


def test_entities_carry_confidence():
    entities, _ = extract_entities("BRCA1 mutations increase breast cancer risk.")
    gene = next(e for e in entities if e.type == "Gene")
    disease = next(e for e in entities if e.type == "Disease")
    assert 0.0 < gene.confidence <= 1.0
    assert 0.0 < disease.confidence <= 1.0
    # Gene allowlist matches are more reliable than disease phrase matches.
    assert gene.confidence >= disease.confidence


def test_extractor_version_is_set():
    assert EXTRACTOR_VERSION.startswith("rule-")


def test_extracts_drug():
    text = "Olaparib may benefit BRCA1-associated breast cancer."
    entities, _ = extract_entities(text)
    assert any(e.type == "Drug" and e.id == "olaparib" for e in entities)
