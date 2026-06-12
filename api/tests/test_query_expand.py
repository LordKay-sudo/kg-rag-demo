from app.rag.query_expand import expand_question, gene_symbols_in_text, normalize_gene_token


def test_brca1_hyphen_normalizes():
    assert normalize_gene_token("BRCA-1") == "BRCA1"
    assert normalize_gene_token("brca-1") == "BRCA1"


def test_expand_question_rewrites_aliases():
    assert "BRCA1" in expand_question("What about BRCA-1 and breast cancer?")


def test_gene_symbols_in_text_finds_canonical():
    symbols = gene_symbols_in_text("Mutations in BRCA-1 increase risk.")
    assert "BRCA1" in symbols
