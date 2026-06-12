from unittest.mock import MagicMock, patch

from app.rag.orchestrator import ask
from app.rag.retriever import RetrievedChunk


def _doc_meta_session(meta_rows):
    """A session whose .run().data() returns document metadata; entities/subgraph empty."""
    session = MagicMock()

    def run(query, **kwargs):
        result = MagicMock()
        if "MATCH (d:Document" in query:
            result.data.return_value = meta_rows
        else:
            result.data.return_value = []
        return result

    session.run.side_effect = run
    return session


def test_citations_include_title_and_reference_url():
    chunks = [
        RetrievedChunk(chunk_id="doc-001-chunk-0", document_id="doc-001",
                       text="BRCA1 increases breast cancer risk.", score=0.8),
    ]
    meta_rows = [{
        "id": "doc-001", "title": "BRCA1 and breast cancer risk",
        "source": "Synthetic demo abstract", "pmid": "20301425", "doi": None, "url": None,
    }]
    session = _doc_meta_session(meta_rows)
    with patch("app.rag.orchestrator.retrieve_chunks", return_value=chunks), \
         patch("app.rag.orchestrator.settings") as s, \
         patch("app.rag.orchestrator.get_session") as mock_get:
        s.min_retrieval_score = 0.25
        s.top_k_chunks = 5
        s.llm_provider = "none"
        mock_get.return_value.__enter__.return_value = session
        result = ask("What links BRCA1 to breast cancer?")

    cite = result["citations"][0]
    assert cite["document_title"] == "BRCA1 and breast cancer risk"
    assert cite["pmid"] == "20301425"
    assert cite["reference_url"] == "https://europepmc.org/article/MED/20301425"


def test_gene_bias_reorders_chunks():
    chunks = [
        RetrievedChunk(chunk_id="c-other", document_id="doc-009", text="KRAS in tumors.", score=0.50),
        RetrievedChunk(chunk_id="c-brca", document_id="doc-001", text="BRCA1 repair.", score=0.45),
    ]
    meta_rows = [{
        "id": "doc-001", "title": "BRCA1 and breast cancer risk",
        "source": None, "pmid": None, "doi": None, "url": None,
    }]
    session = _doc_meta_session(meta_rows)

    def run(query, **kwargs):
        result = MagicMock()
        if "MENTIONS" in query and "ontology_id IN" in query:
            result.data.return_value = [{"chunk_id": "c-brca"}]
        elif "MATCH (d:Document" in query:
            result.data.return_value = meta_rows
        else:
            result.data.return_value = []
        return result

    session.run.side_effect = run

    with patch("app.rag.orchestrator.retrieve_chunks", return_value=chunks), \
         patch("app.rag.orchestrator.settings") as s, \
         patch("app.rag.orchestrator.get_session") as mock_get:
        s.min_retrieval_score = 0.25
        s.top_k_chunks = 5
        s.llm_provider = "none"
        mock_get.return_value.__enter__.return_value = session
        result = ask("Tell me about BRCA1", gene_id="BRCA1")

    assert result["citations"][0]["chunk_id"] == "c-brca"


def test_compact_mode_caps_citations_and_flags_insufficient():
    chunks = [
        RetrievedChunk(chunk_id="c1", document_id="doc-001", text="x" * 200, score=0.28),
        RetrievedChunk(chunk_id="c2", document_id="doc-001", text="y" * 200, score=0.27),
        RetrievedChunk(chunk_id="c3", document_id="doc-001", text="z" * 200, score=0.26),
    ]
    meta_rows = [{"id": "doc-001", "title": "T", "source": None, "pmid": None, "doi": None, "url": None}]
    session = _doc_meta_session(meta_rows)
    with patch("app.rag.orchestrator.retrieve_chunks", return_value=chunks), \
         patch("app.rag.orchestrator.settings") as s, \
         patch("app.rag.orchestrator.get_session") as mock_get:
        s.min_retrieval_score = 0.30
        s.widen_min_retrieval_score = 0.15
        s.compact_top_k = 2
        s.compact_snippet_chars = 50
        s.top_k_chunks = 5
        s.llm_provider = "none"
        mock_get.return_value.__enter__.return_value = session
        result = ask("BRCA1?", compact=True)

    assert result["insufficient_evidence"] is True
    assert len(result["citations"]) <= 2
    assert len(result["citations"][0]["snippet"]) <= 50
    assert "[Partial evidence" in result["answer"]
