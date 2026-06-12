from app.identifiers import resolve_disease_id, resolve_entity_id, resolve_gene_id


def test_gene_symbol_resolves_to_ensembl():
    assert resolve_gene_id("BRCA1") == "ENSG00000012048"
    assert resolve_gene_id("brca1") == "ENSG00000012048"


def test_disease_slug_resolves_to_ontology():
    assert resolve_disease_id("breast_cancer") == "EFO_0000305"
    assert resolve_disease_id("alzheimer_disease") == "MONDO_0004975"


def test_unknown_symbol_returns_none():
    assert resolve_gene_id("ZZZ9") is None
    assert resolve_disease_id("not_a_disease") is None


def test_resolve_entity_id_dispatches_by_type():
    assert resolve_entity_id("Gene", "TP53") == "ENSG00000141510"
    assert resolve_entity_id("Disease", "melanoma") == "EFO_0000756"
    assert resolve_entity_id("Drug", "olaparib") is None


def test_brca1_id_matches_bioinsight_join_key():
    # BioInsight uses ENSG00000012048 for BRCA1; the shared key must match.
    assert resolve_gene_id("BRCA1") == "ENSG00000012048"
