from datetime import datetime, timezone

from app.evidence_sources import (
    SourceDocument,
    content_fingerprint,
    corroboration_groups,
    documents_to_evidence,
    normalize_source_identity,
)


def test_content_fingerprint_is_stable():
    assert content_fingerprint("hello   world") == content_fingerprint(" hello world ")


def test_source_identity_normalizes_domain():
    assert normalize_source_identity("Example", "https://www.Example.com/story") == "example.com"


def test_documents_become_provenance_rich_evidence():
    document = SourceDocument(
        source="Example News",
        title="Test",
        content="A factual source document.",
        retrieved_at=datetime(2026, 9, 8, tzinfo=timezone.utc).isoformat(),
        observed_at=datetime(2026, 9, 7, tzinfo=timezone.utc).isoformat(),
        url="https://example.com/story",
        point_in_time=True,
    )
    evidence = documents_to_evidence([document], "The reported fact is true.")
    assert evidence[0]["provenance"]["source_identity"] == "example.com"
    assert evidence[0]["provenance"]["content_hash"]
    assert evidence[0]["provenance"]["point_in_time"] is True


def test_syndicated_copy_is_not_counted_as_independent_source():
    items = [
        {"evidence_id": "a", "source": "Wire", "claim": "Same claim", "provenance": {"source_identity": "wire.example", "content_hash": "abc"}},
        {"evidence_id": "b", "source": "Publisher", "claim": "Same claim", "provenance": {"source_identity": "publisher.example", "content_hash": "abc", "independent": False}},
    ]
    groups = corroboration_groups(items)
    assert len(groups) == 1
    assert groups[0]["independent_source_count"] == 1


def test_distinct_content_remains_distinct():
    items = [
        {"evidence_id": "a", "source": "A", "claim": "Same claim", "provenance": {"source_identity": "a", "content_hash": "abc"}},
        {"evidence_id": "b", "source": "B", "claim": "Same claim", "provenance": {"source_identity": "b", "content_hash": "xyz"}},
    ]
    assert len(corroboration_groups(items)) == 2
