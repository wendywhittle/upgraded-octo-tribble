from datetime import datetime, timezone, timedelta

from app.evidence import corroborate_evidence, validate_evidence


NOW = datetime(2026, 9, 8, 15, 0, tzinfo=timezone.utc)


def item(evidence_id, source, claim, observed_at, url=None, publisher=None):
    provenance = {"type": "external", "point_in_time": True}
    if url:
        provenance["url"] = url
    if publisher:
        provenance["publisher"] = publisher
    return {
        "evidence_id": evidence_id,
        "source": source,
        "claim": claim,
        "observed_at": observed_at,
        "retrieved_at": NOW.isoformat(),
        "provenance": provenance,
    }


def test_point_in_time_rejects_evidence_from_future():
    future = (NOW + timedelta(minutes=1)).isoformat()
    report = validate_evidence(item("E1", "Source A", "Claim", future), now=NOW)
    assert report["valid"] is False
    assert any("future" in error for error in report["errors"])


def test_point_in_time_requires_explicit_provenance():
    evidence = item("E1", "Source A", "Claim", NOW.isoformat())
    evidence["provenance"]["point_in_time"] = False
    report = validate_evidence(evidence, now=NOW)
    assert report["valid"] is True
    assert report["decision_usable"] is True
    assert report["warnings"]


def test_syndicated_copies_do_not_count_as_independent_sources():
    observed = (NOW - timedelta(hours=1)).isoformat()
    evidence = [
        item("E1", "Reuters", "Company X reported earnings", observed, "https://reuters.example/story", "Reuters"),
        item("E2", "News Site", "Company X reported earnings", observed, "https://news.example/story", "News Site"),
        item("E3", "Official Filing", "Company X reported earnings", observed, "https://filing.example/10q", "Company X"),
    ]
    evidence[1]["provenance"]["parent_evidence_id"] = "E1"
    result = corroborate_evidence(evidence, now=NOW)
    assert result["unique_source_count"] == 2
    assert result["independent_evidence_count"] == 2
    assert "E2" in result["dependent_evidence_ids"]


def test_different_claims_remain_distinct_even_from_same_source():
    observed = (NOW - timedelta(hours=1)).isoformat()
    evidence = [
        item("E1", "Source A", "Revenue increased", observed),
        item("E2", "Source A", "Margins decreased", observed),
    ]
    result = corroborate_evidence(evidence, now=NOW)
    assert result["claim_group_count"] == 2
    assert result["independent_evidence_count"] == 2
