import pytest

from app.capital_allocation import assess_allocation, capital_allocation_manifest


def test_empty_allocation_is_explicit_no_data():
    result = assess_allocation([])
    assert result["status"] == "NO_DATA"
    assert result["investment_authority"] is False


def test_allocation_reports_concentration_and_unallocated_weight():
    result = assess_allocation([
        {"name": "CRE", "weight": 0.60, "max_weight": 0.70},
        {"name": "Capital", "weight": 0.25, "max_weight": 0.40},
    ])
    assert result["weight_sum"] == pytest.approx(0.85)
    assert result["cash_or_unallocated_weight"] == pytest.approx(0.15)
    assert result["concentration"] == pytest.approx(0.60)
    assert result["limit_breaches"] == []


def test_limit_breach_is_visible_not_repaired():
    result = assess_allocation([
        {"name": "CRE", "weight": 0.75, "max_weight": 0.60},
    ])
    assert result["status"] == "REVIEW"
    assert result["limit_breaches"][0]["name"] == "CRE"
    assert result["positions"][0]["weight"] == pytest.approx(0.75)


def test_missing_weight_is_not_inferred():
    with pytest.raises(ValueError, match="missing weight"):
        assess_allocation([{"name": "CRE"}])


def test_manifest_is_research_only():
    manifest = capital_allocation_manifest()
    assert manifest["research_only"] is True
    assert manifest["investment_authority"] is False
    assert "submit_orders" in manifest["does_not"]
