from datetime import datetime, timezone

from app.evidence_pipeline import acquire_evidence
from app.evidence_sources import SourceDocument
from app.source_adapters import StaticEvidenceSource


NOW = datetime(2026, 9, 8, 14, 0, tzinfo=timezone.utc)


def test_acquisition_flows_through_integrity_gate():
    source = StaticEvidenceSource([
        SourceDocument(
            source="Research Feed",
            title="Market update",
            content="Equity markets rise.",
            retrieved_at="2026-09-08T13:00:00+00:00",
            observed_at="2026-09-08T12:00:00+00:00",
            source_id="item-1",
            provenance_type="external_source",
            point_in_time=True,
        )
    ])
    result = acquire_evidence(
        source,
        query="market",
        claim="Equity markets rise.",
        now=NOW,
    )
    assert result["decision_usable"] is True
    assert result["usable_evidence_count"] == 1
    assert result["reasoning_applied"] is False
    assert result["execution_capability"] is False
    assert result["validation"][0]["valid"] is True


def test_stale_acquired_evidence_is_blocked():
    source = StaticEvidenceSource([
        SourceDocument(
            source="Old Feed",
            title="Old market update",
            content="Equity markets rise.",
            retrieved_at="2026-09-01T13:00:00+00:00",
            observed_at="2026-09-01T12:00:00+00:00",
            source_id="old-1",
            provenance_type="external_source",
            point_in_time=True,
        )
    ])
    result = acquire_evidence(
        source,
        query="market",
        claim="Equity markets rise.",
        now=NOW,
    )
    assert result["decision_usable"] is False
    assert result["usable_evidence_count"] == 0
    assert result["validation"][0]["valid"] is False
