from datetime import datetime, timezone

import pytest

from app.scenario_analysis import (
    CREScenarioAnalysis,
    ScenarioOverride,
    build_cre_scenario,
    compare_scenarios,
)
from app.underwriting import (
    AcquisitionTerms,
    OperatingAssumptions,
    PropertyIdentity,
    UnderwritingProvenance,
    ValuationAssumptions,
    build_cre_underwriting,
)


def underwriting():
    provenance = UnderwritingProvenance(status="assumed")
    return build_cre_underwriting(
        underwriting_id="uw-scenario-1",
        property=PropertyIdentity(property_id="property-1"),
        acquisition=AcquisitionTerms(
            purchase_price=10_000_000,
            acquisition_costs=100_000,
            provenance=provenance,
        ),
        operations=OperatingAssumptions(
            gross_revenue=1_000_000,
            operating_expenses=300_000,
            provenance=provenance,
        ),
        valuation=ValuationAssumptions(exit_cap_rate=0.07, provenance=provenance),
    )


def fixed_time():
    return datetime(2026, 9, 11, tzinfo=timezone.utc)


def test_valid_scenario_with_explicit_overrides_recalculates_existing_engine():
    scenario = build_cre_scenario(
        scenario_id="downside-1",
        scenario_name="Downside",
        scenario_type="downside",
        underwriting=underwriting(),
        overrides=(
            ScenarioOverride(input_name="gross_potential_income", value=900_000),
            ScenarioOverride(input_name="vacancy_credit_loss", value=90_000),
            ScenarioOverride(input_name="operating_expenses", value=330_000),
            ScenarioOverride(input_name="property_value", value=10_000_000),
        ),
        created_at=fixed_time(),
    )
    values = {item.calculation_type: item.value for item in scenario.calculations}
    assert values["effective_gross_income"] == 810_000
    assert values["net_operating_income"] == 480_000
    assert values["cap_rate"] == pytest.approx(0.048)
    assert scenario.status == "scenario"
    assert scenario.provenance.formula_version == "cre-underwriting-v1"


def test_same_inputs_and_overrides_are_deterministic():
    kwargs = dict(
        scenario_name="Base",
        scenario_type="base",
        underwriting=underwriting(),
        overrides=(ScenarioOverride(input_name="vacancy_credit_loss", value=50_000),),
        created_at=fixed_time(),
    )
    first = build_cre_scenario(scenario_id="base-identity", **kwargs)
    second = build_cre_scenario(scenario_id="base-identity", **kwargs)
    assert first.inputs == second.inputs
    assert first.calculations == second.calculations
    assert first.model_dump(mode="json") == second.model_dump(mode="json")
    assert first.calculations[0].value == 950_000


def test_downside_does_not_mutate_base_underwriting():
    base = underwriting()
    original = base.model_dump(mode="json")
    build_cre_scenario(
        scenario_id="downside-2",
        scenario_name="Downside",
        scenario_type="downside",
        underwriting=base,
        overrides=(ScenarioOverride(input_name="operating_expenses", value=500_000),),
        created_at=fixed_time(),
    )
    assert base.model_dump(mode="json") == original
    assert base.operations.operating_expenses == 300_000


def test_only_explicitly_overridden_values_change():
    scenario = build_cre_scenario(
        scenario_id="upside-1",
        scenario_name="Upside",
        scenario_type="upside",
        underwriting=underwriting(),
        overrides=(ScenarioOverride(input_name="operating_expenses", value=250_000),),
        created_at=fixed_time(),
    )
    assert scenario.inputs.gross_potential_income == 1_000_000
    assert scenario.inputs.operating_expenses == 250_000
    assert scenario.inputs.property_value == 10_000_000
    assert scenario.inputs.vacancy_credit_loss is None


def test_missing_inputs_remain_unresolved_and_are_not_zero():
    scenario = build_cre_scenario(
        scenario_id="base-missing",
        scenario_name="Base",
        scenario_type="base",
        underwriting=underwriting(),
        created_at=fixed_time(),
    )
    egi = scenario.calculations[0]
    assert egi.status == "unresolved"
    assert egi.value is None
    assert "vacancy_credit_loss" in egi.missing_inputs


def test_duplicate_overrides_are_rejected():
    with pytest.raises(ValueError, match="at most once"):
        build_cre_scenario(
            scenario_id="duplicate",
            scenario_name="Downside",
            scenario_type="downside",
            underwriting=underwriting(),
            overrides=(
                ScenarioOverride(input_name="operating_expenses", value=300_000),
                ScenarioOverride(input_name="operating_expenses", value=400_000),
            ),
        )


def test_scenario_is_immutable_and_serializable():
    scenario = build_cre_scenario(
        scenario_id="immutable",
        scenario_name="Base",
        scenario_type="base",
        underwriting=underwriting(),
        overrides=(ScenarioOverride(input_name="vacancy_credit_loss", value=50_000),),
        created_at=fixed_time(),
    )
    with pytest.raises((TypeError, ValueError)):
        scenario.scenario_name = "changed"
    assert scenario.model_dump(mode="json") == scenario.model_dump(mode="json")


def test_provenance_traces_base_overrides_and_calculations():
    scenario = build_cre_scenario(
        scenario_id="trace-1",
        scenario_name="Stress",
        scenario_type="stress",
        underwriting=underwriting(),
        overrides=(ScenarioOverride(input_name="vacancy_credit_loss", value=150_000),),
        created_at=fixed_time(),
    )
    assert scenario.base_underwriting_ref == "underwriting:uw-scenario-1"
    assert scenario.provenance.override_refs == ("override:trace-1:vacancy_credit_loss",)
    assert scenario.provenance.calculation_refs[0] == "calculation:trace-1:effective_gross_income"
    assert scenario.calculations[0].input_refs == ("scenario:trace-1",)


def test_scenario_is_distinct_from_evidence_finding_recommendation_and_authorization():
    scenario = build_cre_scenario(
        scenario_id="epistemic-1",
        scenario_name="Adversarial",
        scenario_type="adversarial",
        underwriting=underwriting(),
        overrides=(ScenarioOverride(input_name="vacancy_credit_loss", value=250_000),),
        created_at=fixed_time(),
    )
    dumped = scenario.model_dump()
    assert dumped["status"] in {"scenario", "unresolved", "superseded"}
    assert "evidence" not in dumped
    assert "finding" not in dumped
    assert "recommendation" not in dumped
    assert dumped["investment_authority"] == "none"
    assert dumped["execution_capability"] is False
    assert dumped["transaction_capability"] is False
    assert dumped["portfolio_mutation"] is False
    assert dumped["authorization_capability"] is False


def test_due_diligence_findings_are_not_automatically_transformed_into_assumptions():
    scenario = build_cre_scenario(
        scenario_id="dd-separation",
        scenario_name="Downside",
        scenario_type="downside",
        underwriting=underwriting(),
        created_at=fixed_time(),
    )
    assert scenario.overrides == ()
    assert scenario.inputs.vacancy_credit_loss is None


def test_comparison_is_descriptive_and_has_no_recommendation_or_ranking():
    base = build_cre_scenario(
        scenario_id="cmp-base",
        scenario_name="Base",
        scenario_type="base",
        underwriting=underwriting(),
        overrides=(ScenarioOverride(input_name="vacancy_credit_loss", value=50_000),),
        created_at=fixed_time(),
    )
    downside = build_cre_scenario(
        scenario_id="cmp-down",
        scenario_name="Downside",
        scenario_type="downside",
        underwriting=underwriting(),
        overrides=(ScenarioOverride(input_name="vacancy_credit_loss", value=150_000),),
        created_at=fixed_time(),
    )
    comparison = compare_scenarios(
        (base, downside),
        comparison_id="comparison-1",
        calculation_types=("effective_gross_income", "net_operating_income"),
        created_at=fixed_time(),
    )
    assert comparison.scenario_ids == ("cmp-base", "cmp-down")
    assert comparison.metrics[0].scenario_values == (("cmp-base", 950_000), ("cmp-down", 850_000))
    dumped = comparison.model_dump()
    assert "recommendation" not in dumped


def test_scenario_module_contains_no_probabilistic_scenario_contract():
    fields = CREScenarioAnalysis.model_fields
    assert "probability" not in fields
    assert "distribution" not in fields
    assert "random_seed" not in fields
    assert "recommendation" not in fields
