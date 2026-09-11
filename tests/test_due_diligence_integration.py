from datetime import datetime, timezone

from app.due_diligence import CREPropertyDueDiligence, DueDiligenceFinding
from app.investment_case import build_structured_investment_case
from app.opportunity import PropertyIdentityReference, build_cre_opportunity
from app.screening import CREOpportunityScreening

NOW = datetime(2026, 9, 11, tzinfo=timezone.utc)


def test_due_diligence_integrates_with_investment_case_without_authority():
    opportunity = build_cre_opportunity(
        opportunity_id="opp-1",
        property=PropertyIdentityReference(property_id="prop-1"),
        created_at=NOW,
    )
    screening = CREOpportunityScreening(
        screening_id="screen-1", opportunity_id="opp-1", created_at=NOW, disposition="PASS"
    )
    diligence = CREPropertyDueDiligence(
        due_diligence_id="dd-1",
        opportunity_id="opp-1",
        property_id="prop-1",
        created_at=NOW,
        findings=[
            DueDiligenceFinding(
                finding_id="f-1",
                category="physical",
                field_name="roof_condition",
                status="unresolved",
                review_status="unresolved",
                finding="Inspection required",
                materiality="high",
                risk_flag="inspection_required",
            )
        ],
    )
    case = build_structured_investment_case(
        question="Should this opportunity proceed?",
        evidence={"items": []},
        agents=[],
        simulation={},
        skeptic={},
        synthesis={"verdict": "NO_DATA"},
        opportunity_deal=opportunity,
        screening=screening,
        due_diligence=diligence,
        created_at=NOW,
    )
    assert case.due_diligence == diligence
    assert case.authority == "none"
    assert case.execution_capability is False
    assert case.portfolio_mutation is False
    assert case.human_decision_gate.required is True


def test_due_diligence_does_not_create_underwriting_assumption():
    diligence = CREPropertyDueDiligence(
        due_diligence_id="dd-2",
        opportunity_id="opp-1",
        created_at=NOW,
        findings=[
            DueDiligenceFinding(
                finding_id="f-2",
                category="physical",
                field_name="roof_replacement",
                status="unresolved",
                review_status="completed",
                finding="Replacement may be required",
                materiality="high",
                risk_flag="deferred_maintenance",
            )
        ],
    )
    assert diligence.findings[0].finding == "Replacement may be required"
    assert not hasattr(diligence.findings[0], "capex_assumption")
