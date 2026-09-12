from app.opportunity_acquisition import RawObservation, acquire, deduplicate, normalize_observation
from app.opportunity_endpoint import build_opportunity_router


def observation():
    return RawObservation(
        source="fixture",
        source_url="https://example.invalid/opportunity/1",
        observed_at="2026-09-12T20:00:00+00:00",
        payload={
            "asset_type": "industrial",
            "location": "Vancouver, WA",
            "asking_price": 10000000,
            "property_attributes": {"noi": 700000},
        },
    )


def test_normalization_preserves_provenance_and_distinguishes_opportunity_from_evidence():
    result = normalize_observation(observation())
    assert result["opportunity_id"].startswith("OPP-")
    assert result["provenance"]["source"] == "fixture"
    assert result["acquisition_status"] == "NORMALIZED"
    assert result["evidence_status"] == "PENDING"


def test_deduplicate_removes_duplicate_fingerprints():
    item = normalize_observation(observation())
    result = deduplicate([item, dict(item)])
    assert len(result) == 1
    assert result[0]["acquisition_status"] == "DEDUPLICATED"


def test_acquisition_is_research_only_and_never_authorizes_execution():
    result = acquire([observation()])
    assert result["deduplicated_count"] == 1
    assert result["opportunity_is_not_evidence"] is True
    assert result["evidence_validation_required"] is True
    assert result["research_only"] is True
    assert result["human_authority_required"] is True
    assert result["autonomous_execution"] is False
    assert result["brokerage_connectivity"] is False
    assert result["portfolio_mutation"] is False
    assert result["investment_authority"] is False


def test_opportunity_router_exposes_acquisition_route():
    router = build_opportunity_router()
    assert "/opportunities/acquire" in {route.path for route in router.routes}
