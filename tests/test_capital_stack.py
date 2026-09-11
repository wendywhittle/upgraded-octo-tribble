from datetime import date, datetime, timezone

import pytest

from app.capital_stack import CapitalStack, LenderEvidence
from app.investment_case import build_structured_investment_case


NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def make_stack():
    return CapitalStack(
        stack_id="stack-1",
        created_at=NOW,
        purchase_price=1_000_000,
        acquisition_costs=25_000,
        total_capitalization=1_025_000,
        debt=650_000,
        sponsor_equity=375_000,
        loan_amount=650_000,
        ltv=0.65,
        interest_rate=0.065,
        term_years=5,
        maturity_date=date(2031, 9, 11),
        dscr=1.35,
        debt_yield=0.09,
        financing_assumptions=["Modeled leverage is 65%."],
        source_refs=["lender-evidence-1"],
        provenance={"source": "research-model"},
    )


def make_lender(status="current"):
    return LenderEvidence(
        evidence_id="lender-evidence-1",
        lender_identity="Example Research Source",
        lender_type="private lender",
        asset_class_focus=["industrial"],
        geography=["Pacific Northwest"],
        minimum_loan_size=500_000,
        maximum_loan_size=5_000_000,
        target_deal_size=2_000_000,
        ltv_range="up to 65%",
        dscr_requirement="1.25x",
        recourse="case-by-case",
        source="published lender criteria",
        source_date=date(2026, 9, 1),
        evidence_status=status,
        confidence=0.8,
        uncertainty=["Terms require transaction-specific confirmation."],
    )


def test_capital_stack_is_analytical_and_immutable():
    stack = make_stack()
    assert stack.ltv == 0.65
    assert stack.authorization == "none"
    assert stack.capital_deployment is False
    with pytest.raises(Exception):
        stack.ltv = 0.70


def test_lender_evidence_is_research_not_commitment():
    evidence = make_lender()
    assert evidence.commitment_status == "research_only"
    assert evidence.authorization == "none"
    assert evidence.source_date == date(2026, 9, 1)
    with pytest.raises(Exception):
        evidence.confidence = 1.0


def test_conflicting_or_changed_lender_evidence_can_coexist_without_overwrite():
    old = make_lender("superseded")
    new = make_lender("current").model_copy(update={"evidence_id": "lender-evidence-2", "source_date": date(2026, 9, 11)})
    assert old.evidence_id != new.evidence_id
    assert old.evidence_status == "superseded"
    assert new.evidence_status == "current"


def test_investment_case_accepts_typed_financing_boundary_and_serializes():
    case = build_structured_investment_case(
        question="Assess financing",
        evidence={"items": [{"evidence_id": "E-1", "source": "primary"}]},
        agents=[{"agent_id": "quant", "assumptions": ["NOI is stable."]}],
        simulation={"scenarios": [], "independent_of_agents": True},
        skeptic={"recommendation": "hold", "challenges": ["Leverage may be fragile."]},
        synthesis={"verdict": "NO_GO", "unresolved_questions": []},
        capital_stack=make_stack(),
        lender_evidence=[make_lender()],
        financing_assumptions=["Lender terms are indicative only."],
        financing_risks=["Refinancing risk remains unresolved."],
        created_at=NOW,
    )
    assert case.capital_stack.loan_amount == 650_000
    assert case.lender_evidence[0].evidence_id == "lender-evidence-1"
    assert "Lender evidence is not present" not in " ".join(case.gaps)
    assert case.recommendation == "NO_GO"
    payload = case.model_dump(mode="json")
    assert payload["capital_stack"]["authorization"] == "none"
    assert payload["lender_evidence"][0]["commitment_status"] == "research_only"
    assert payload["human_decision_gate"]["authorized"] is False
