from datetime import datetime, timezone

from app.investment_case import build_structured_investment_case
from app.scenario_analysis import ScenarioOverride, build_cre_scenario
from app.underwriting import (
    AcquisitionTerms,
    OperatingAssumptions,
    PropertyIdentity,
    UnderwritingProvenance,
    ValuationAssumptions,
    build_cre_underwriting,
)


def test_structured_investment_case_can_carry_typed_cre_scenarios_without_authority():
    provenance = UnderwritingProvenance(status="assumed")
    underwriting = build_cre_underwriting(
        underwriting_id="uw-case-scenario",
        property=PropertyIdentity(property_id="property-case"),
        acquisition=AcquisitionTerms(purchase_price=5_000_000, provenance=provenance),
        operations=OperatingAssumptions(
            gross_revenue=500_000,
            operating_expenses=150_000,
            provenance=provenance,
        ),
        valuation=ValuationAssumptions(provenance=provenance),
    )
    scenario = build_cre_scenario(
        scenario_id="case-downside",
        scenario_name="Downside",
        scenario_type="downside",
        underwriting=underwriting,
        overrides=(ScenarioOverride(input_name="vacancy_credit_loss", value=50_000),),
        created_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
    )
    case = build_structured_investment_case(
        question="Evaluate this CRE opportunity",
        evidence={"items": []},
        agents=[],
        simulation={},
        skeptic={},
        synthesis={"verdict": "INVESTIGATE"},
        underwriting=underwriting,
        cre_scenarios=[scenario],
        created_at=datetime(2026, 9, 11, tzinfo=timezone.utc),
    )
    assert case.cre_scenarios == [scenario]
    assert case.authority == "none"
    assert case.execution_capability is False
    assert case.portfolio_mutation is False
    assert case.human_decision_gate.status == "pending"
