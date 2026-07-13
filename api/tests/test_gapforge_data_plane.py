"""Tests for PeerLens filter and ClinicalTrials formatting."""
from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.ingest.clinicaltrials import format_ct_document
from app.ingest.peerlens_filter import PeerLensFilterResult, filter_paper


def test_format_ct_document():
    text = format_ct_document(
        nct_id="NCT00105547",
        title="Example",
        summary="Brief summary",
        phase="PHASE3",
        status="COMPLETED",
        conditions=["Alzheimer Disease"],
    )
    assert "NCT: NCT00105547" in text
    assert "ClinicalTrials.gov" in text
    assert "Brief summary" in text


@patch("app.ingest.peerlens_filter.analyze_identifier")
def test_filter_blocks_retraction(mock_analyze):
    mock_analyze.return_value = {
        "signals": [
            {"id": "paper_retracted", "severity": "concern", "message": "Retracted"},
        ]
    }
    result = filter_paper("10.0/example")
    assert isinstance(result, PeerLensFilterResult)
    assert result.allowed is False
    assert any("retracted" in r for r in result.reasons)


@patch("app.ingest.peerlens_filter.analyze_identifier")
def test_filter_fail_open(mock_analyze):
    mock_analyze.return_value = None
    result = filter_paper("10.0/example", fail_open=True)
    assert result.allowed is True
    assert result.skipped is True
