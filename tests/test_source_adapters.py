from datetime import datetime, timezone

from app.evidence_sources import SourceDocument
from app.source_adapters import StaticEvidenceSource, source_status


def document(title, content):
    return SourceDocument(
        source="Test Source",
        title=title,
        content=content,
        retrieved_at=datetime(2026, 9, 8, tzinfo=timezone.utc).isoformat(),
        observed_at=datetime(2026, 9, 8, tzinfo=timezone.utc).isoformat(),
        provenance_type="external_source",
        point_in_time=True,
    )


def test_static_source_filters_and_limits():
    source = StaticEvidenceSource([document("Alpha", "market growth"), document("Beta", "credit risk")])
    result = source.acquire("growth", limit=1)
    assert len(result) == 1
    assert result[0].title == "Alpha"


def test_source_status_is_read_only():
    status = source_status(StaticEvidenceSource([]))
    assert status["read_only"] is True
    assert status["execution_capability"] is False
