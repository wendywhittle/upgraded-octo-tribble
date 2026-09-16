from dataclasses import FrozenInstanceError

import pytest

from app.capital_structure import (
    AnalyticalValue,
    ValueClassification,
    build_capital_structure_scenario,
    compare_capital_structures,
)


def evidence(**overrides):
    item = {
        "evidence_id": "E-FIN-1",
        "source": "provider-source",
        "observed_at": "2026-09-15T11:00:00+00:00",
        "claim": {
            "financing_type": "senior_debt",
            "loan_to_value": 70.0,
            "loan_to_cost": 75.0,
            "interest_rate": "floating",
            "term": "24 months",
            "amortization": "interest-only",
        },
        "provenance": {
            "type": "external_source",
            "point_in_time": True,
            "provider_id": "provider-alpha",
            "observation_id": "fin-1",
            "validation_status": "VALIDATED",
        },
        "evidence_validation": {"decision_usable": True},
    }
    item.update(overrides)
    return item


def test_only_validated_financing_evidence_can_enter_analysis():
    with pytest.raises(ValueError, match="validated financing evidence"):
        build_capital_structure_scenario("A", "Senior debt", evidence(
            evidence_validation={"decision_usable": False}
        ))


def test_observed_values_retain_evidence_identity():
    scenario = build_capital_structure_scenario("A", "Senior debt", evidence())
    assert scenario.loan_to_value.classification == ValueClassification.OBSERVED
    assert scenario.loan_to_value.source_evidence_ids == ("E-FIN-1",)
    assert scenario.financing_type.value == "senior_debt"
    assert scenario.interest_rate.value == "floating"
    assert scenario.term.value == "24 months"
    assert scenario.amortization.value == "interest-only"


def test_ltv_derives_loan_amount_and_required_equity():
    scenario = build_capital_structure_scenario(
        "A", "Senior debt", evidence(), property_value=10_000_000, total_project_cost=12_000_000
    )
    assert scenario.loan_amount.value == 7_000_000
    assert scenario.loan_amount.classification == ValueClassification.DERIVED
    assert scenario.required_equity.value == 5_000_000
    assert scenario.required_equity.classification == ValueClassification.DERIVED
    assert scenario.loan_to_cost.value == pytest.approx(58.3333333333)
    assert scenario.loan_to_cost.classification == ValueClassification.DERIVED


def test_missing_terms_remain_unknown():
    item = evidence(claim={"financing_type": "equity", "loan_to_value": None})
    scenario = build_capital_structure_scenario("A", "Equity", item)
    assert scenario.loan_amount.value is None
    assert scenario.interest_rate.classification == ValueClassification.UNKNOWN
    assert "interest_rate" in scenario.unknowns
    assert "loan_amount" in scenario.unknowns


def test_explicit_assumptions_are_distinct_from_observed_values():
    scenario = build_capital_structure_scenario(
        "A", "Bridge", evidence(),
        assumptions={
            "refinancing_assumption": "refinance at maturity",
            "maturity": "24 months",
            "sensitivity_parameters": ("interest_rate", "LTV"),
        },
    )
    assert scenario.term.classification == ValueClassification.OBSERVED
    assert scenario.maturity.classification == ValueClassification.ASSUMED
    assert scenario.refinancing_assumption.classification == ValueClassification.ASSUMED
    assert scenario.sensitivity_parameters == ("interest_rate", "LTV")


def test_analysis_model_is_immutable():
    value = AnalyticalValue(value=70.0, classification=ValueClassification.OBSERVED, source_evidence_ids=("E1",))
    with pytest.raises(FrozenInstanceError):
        value.value = 80.0


def test_multiple_provider_types_use_same_contract():
    providers = ("private-lender", "bank", "family-office", "institutional-debt", "equity-provider", "strategic-capital")
    scenarios = [
        build_capital_structure_scenario(
            provider, provider, evidence(provenance={
                "type": "external_source", "point_in_time": True,
                "provider_id": provider, "observation_id": provider,
                "validation_status": "VALIDATED",
            })
        )
        for provider in providers
    ]
    assert [s.financing_type.value for s in scenarios] == ["senior_debt"] * len(providers)


def test_comparison_does_not_rank_or_select():
    a = build_capital_structure_scenario("A", "Lower leverage", evidence(), property_value=10_000_000, total_project_cost=10_000_000)
    b = build_capital_structure_scenario("B", "Higher leverage", evidence(), property_value=10_000_000, total_project_cost=10_000_000)
    result = compare_capital_structures((a, b))
    assert result["pairwise_comparisons"]
    assert result["ranking"] is None
    assert result["selected_scenario"] is None
    assert result["recommendation"] is None
    assert result["research_only"] is True
    assert result["investment_authority"] is False
    assert result["financing_authority"] is False
    assert result["execution_capability"] is False


def test_explicit_assumptions_are_not_presented_as_evidence():
    scenario = build_capital_structure_scenario(
        "A", "Scenario", evidence(), assumptions={"maturity": "24 months"}
    )
    assert scenario.maturity.classification == ValueClassification.ASSUMED
    assert scenario.maturity.source_evidence_ids == ()
    assert scenario.maturity.assumption == "explicit analytical maturity assumption"
