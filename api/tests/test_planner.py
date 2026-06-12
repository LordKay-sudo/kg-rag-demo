from unittest.mock import patch

from app.rag.planner import plan_question


def test_plan_decomposes_gene_disease_question():
    plan = plan_question("What links BRCA1 to breast cancer?")
    assert plan["intent"] == "gene_disease"
    assert len(plan["steps"]) >= 2
    assert plan["suggested_gene_id"] == "BRCA1"
    assert plan["suggested_disease_id"] == "breast_cancer"
    assert plan["expanded_question"] == plan["question"]


def test_plan_hyphenated_gene():
    plan = plan_question("Tell me about BRCA-1")
    assert plan["suggested_gene_id"] == "BRCA1"


@patch("app.rag.planner.graph_evidence_is_weak", return_value=True)
def test_plan_sets_widen_when_graph_weak(_mock):
    plan = plan_question("BRCA1 associations", gene_id="BRCA1")
    assert plan["widen_retrieval"] is True
