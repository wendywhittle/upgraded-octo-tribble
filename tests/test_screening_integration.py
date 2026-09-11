from datetime import datetime, timezone

from app.investment_case import build_structured_investment_case
from app.screening import build_cre_opportunity_screening

NOW = datetime(2026, 9, 11, 15, 0, tzinfo=timezone.utc)


def test_screening_can_flow_into_investment_case_without_authority():
    screening = build_cre_opportunity_screening(
        screening_id="SCREEN-1",
        opportunity_id="OPP-1",
        disposition="PASS",
        created_at=NOW,
    )
    case = build_structured_investment_case(
        question="Should this CRE opportunity advance to underwriting?",
        evidence={"items": []},
        agents=[],
        simulation={},
        skeptic={},
        synthesis={"verdict": "INVESTIGATE"},
        screening=screening,
        created_at=NOW,
    )
    assert case.screening is screening
    assert case.screening.opportunity_id == "OPP-1"
    assert case.authority == "none"
    assert case.execution_capability is False
    assert case.portfolio_mutation is False
    assert case.human_decision_gate.required is True
    assert case.human_decision_gate.authorized is False


def test_missing_screening_is_an_explicit_case_gap():
    case = build_structured_investment_case(
        question="Screen this opportunity",
        evidence={"items": []},
        agents=[],
        simulation={},
        skeptic={},
        synthesis={"verdict": "NO_DATA"},
        created_at=NOW,
    )
    assert case.screening is None
    assert "CRE opportunity screening is not yet supplied." in case.gaps
