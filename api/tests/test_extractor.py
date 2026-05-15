from app.ingest.extractor import extract_entities


def test_extracts_gene_and_disease():
    text = "BRCA1 mutations increase breast cancer risk."
    entities, relations = extract_entities(text)
    types = {e.type for e in entities}
    assert "Gene" in types
    assert "Disease" in types
    assert any(r.relation == "ASSOCIATED_WITH" for r in relations)


def test_extracts_drug():
    text = "Olaparib may benefit BRCA1-associated breast cancer."
    entities, _ = extract_entities(text)
    assert any(e.type == "Drug" and e.id == "olaparib" for e in entities)
