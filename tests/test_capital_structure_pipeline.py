import pytest

from app.capital_structure_pipeline import build_capital_structure_context, merge_research_context


def scenario():
    return {
        "scenario_id": "A",
        "label": "Senior debt",
        "financing_type": {
            "value": "senior_debt",
            "classification": "observed",
            "source_evidence_ids": ["E-FIN-1"],
            "assumption": None,
        },
        "loan_to_value": {
            "value": 70.0,
            "classification": "observed",
            "source_evidence_ids": ["E-FIN-1"],
            "assumption": None,
        },
        "loan_amount": {
            "value": 7_000_000,
            "classification": "derived",
            "source_evidence_ids": ["E-FIN-1"],
            "assumption": None,
        },
        "interest_rate": {
            "value": 7.0,
            "classification": "assumed",
            "source_evidence_ids": [],
            "assumption": "explicit sensitivity case",
        },
        "amortization": {
            "value": None,
            "classification": "unknown",
            "source_evidence_ids": [],
            "assumption": None,
        },
    }


def test_context_preserves_epistemic_classes_and_provenance():
    context = build_capital_structure_context([scenario()])
    assert context["source_evidence_ids"] == ["E-FIN-1"]
    assert context["epistemic_classes"] == ["observed", "derived", "assumed", "unknown"]
    assert context["scenarios"][0]["loan_to_value"]["classification"] == "observed"
    assert context["scenarios"][0]["loan_amount"]["classification"] == "derived"
    assert context["scenarios"][0]["interest_rate"]["classification"] == "assumed"
    assert context["scenarios"][0]["amortization"]["classification"] == "unknown"


def test_observed_values_require_provenance():
    bad = scenario()
    bad["loan_to_value"]["source_evidence_ids"] = []
    with pytest.raises(ValueError, match="lacks evidence provenance"):
        build_capital_structure_context([bad])


def test_context_has_no_decision_or_execution_authority():
    context = build_capital_structure_context([scenario()])
    assert context["analytical_only"] is True
    assert context["recommendation"] is None
    assert context["ranking"] is None
    assert context["selected_scenario"] is None
    assert context["financing_authority"] is False
    assert context["investment_authority"] is False
    assert context["execution_capability"] is False
    assert context["portfolio_mutation"] is False


def test_multiple_structures_remain_pairwise_without_selection():
    left = scenario()
    right = scenario()
    right["scenario_id"] = "B"
    context = build_capital_structure_context(
        [left, right],
        pairwise_comparisons=[{"left": "A", "right": "B", "differences": {"loan_amount": {"value": 500000, "status": "DERIVED"}}}],
    )
    assert len(context["scenarios"]) == 2
    assert context["pairwise_comparisons"][0]["left"] == "A"
    assert context["pairwise_comparisons"][0]["right"] == "B"
    assert context["selected_scenario"] is None


def test_merge_keeps_existing_research_context():
    merged = merge_research_context({"asset": "Example Asset"}, build_capital_structure_context([scenario()]))
    assert merged["asset"] == "Example Asset"
    assert "capital_structure" in merged
    assert merged["capital_structure"]["source_evidence_ids"] == ["E-FIN-1"]
