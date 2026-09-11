from pathlib import Path

import pytest

from app.workflow import (
    ActorType,
    AuthorizationDecision,
    AuthorizationGate,
    Opportunity,
    WorkflowError,
    WorkflowService,
    WorkflowState,
    WorkflowStore,
)


def service(tmp_path: Path) -> WorkflowService:
    return WorkflowService(WorkflowStore(tmp_path / "workflow.jsonl"))


def move(svc, deal_id, state, reason="system step", actor_type=ActorType.SYSTEM, auth=None):
    return svc.transition(deal_id, state, "workflow", actor_type, reason, auth)


def test_gate_one_requires_human_authorization(tmp_path):
    svc = service(tmp_path)
    deal = svc.create_deal(Opportunity(name="Synthetic CRE opportunity"))
    move(svc, deal.deal_id, WorkflowState.SCREENED)
    move(svc, deal.deal_id, WorkflowState.AWAITING_UNDERWRITING_APPROVAL)

    with pytest.raises(WorkflowError, match="Human authorization required"):
        move(svc, deal.deal_id, WorkflowState.UNDERWRITING)

    with pytest.raises(WorkflowError, match="Only a human"):
        svc.authorize(
            deal.deal_id, AuthorizationGate.UNDERWRITING, AuthorizationDecision.APPROVE,
            "agent-1", ActorType.AGENT, "agent recommendation",
        )

    auth = svc.authorize(
        deal.deal_id, AuthorizationGate.UNDERWRITING, AuthorizationDecision.APPROVE,
        "human-operator", ActorType.HUMAN, "Proceed to formal underwriting.",
    )
    result = move(svc, deal.deal_id, WorkflowState.UNDERWRITING, auth=auth.authorization_id)
    assert result.state is WorkflowState.UNDERWRITING


def test_capital_and_investment_gates_are_enforced(tmp_path):
    svc = service(tmp_path)
    deal = svc.create_deal(Opportunity(name="Synthetic CRE opportunity"))
    for state in (
        WorkflowState.SCREENED,
        WorkflowState.AWAITING_UNDERWRITING_APPROVAL,
    ):
        deal = move(svc, deal.deal_id, state)
    auth1 = svc.authorize(deal.deal_id, AuthorizationGate.UNDERWRITING, AuthorizationDecision.APPROVE,
                          "human", ActorType.HUMAN, "Proceed.")
    deal = move(svc, deal.deal_id, WorkflowState.UNDERWRITING, auth=auth1.authorization_id)
    for state in (WorkflowState.SIMULATION, WorkflowState.CONTRARIAN_REVIEW, WorkflowState.CAPITAL_STACK_ANALYSIS,
                  WorkflowState.AWAITING_CAPITAL_APPROVAL):
        deal = move(svc, deal.deal_id, state)

    with pytest.raises(WorkflowError, match="Human authorization required"):
        move(svc, deal.deal_id, WorkflowState.INVESTMENT_COMMITTEE)

    auth2 = svc.authorize(deal.deal_id, AuthorizationGate.CAPITAL_STRUCTURE, AuthorizationDecision.APPROVE,
                          "human", ActorType.HUMAN, "Approve proposed capital structure.",
                          scope={"capital_stack_version": 1})
    deal = move(svc, deal.deal_id, WorkflowState.INVESTMENT_COMMITTEE, auth=auth2.authorization_id)
    deal = move(svc, deal.deal_id, WorkflowState.AWAITING_INVESTMENT_APPROVAL)

    with pytest.raises(WorkflowError, match="Human authorization required"):
        move(svc, deal.deal_id, WorkflowState.APPROVED)

    auth3 = svc.authorize(deal.deal_id, AuthorizationGate.INVESTMENT, AuthorizationDecision.APPROVE,
                          "human", ActorType.HUMAN, "Approve investment and portfolio creation.")
    deal = move(svc, deal.deal_id, WorkflowState.APPROVED, auth=auth3.authorization_id)
    assert deal.state is WorkflowState.APPROVED


def test_portfolio_creation_cannot_precede_investment_approval(tmp_path):
    svc = service(tmp_path)
    deal = svc.create_deal(Opportunity(name="Synthetic CRE opportunity"))
    with pytest.raises(WorkflowError, match="Illegal transition"):
        move(svc, deal.deal_id, WorkflowState.PORTFOLIO_CREATED)


def test_no_go_and_rejected_are_first_class_persistent_outcomes(tmp_path):
    svc = service(tmp_path)
    no_go = svc.create_deal(Opportunity(name="No-go opportunity"))
    no_go = move(svc, no_go.deal_id, WorkflowState.NO_GO, reason="Insufficient margin of safety")
    assert no_go.state is WorkflowState.NO_GO
    rejected = svc.create_deal(Opportunity(name="Rejected opportunity"))
    rejected = move(svc, rejected.deal_id, WorkflowState.REJECTED, reason="Outside mandate")
    assert rejected.state is WorkflowState.REJECTED
    assert svc.get_deal(no_go.deal_id).state is WorkflowState.NO_GO
    assert svc.get_deal(rejected.deal_id).state is WorkflowState.REJECTED


def test_audit_records_creation_authorization_and_transition(tmp_path):
    svc = service(tmp_path)
    deal = svc.create_deal(Opportunity(name="Audited opportunity"))
    move(svc, deal.deal_id, WorkflowState.SCREENED)
    events = svc.audit(deal.deal_id)
    assert [event["event_type"] for event in events] == ["DEAL_CREATED", "STATE_TRANSITIONED"]
    assert events[1]["previous_state"] == WorkflowState.DEAL_DISCOVERED.value
    assert events[1]["new_state"] == WorkflowState.SCREENED.value


def test_authorization_is_bound_to_current_object_version(tmp_path):
    svc = service(tmp_path)
    deal = svc.create_deal(Opportunity(name="Versioned opportunity"))
    move(svc, deal.deal_id, WorkflowState.SCREENED)
    move(svc, deal.deal_id, WorkflowState.AWAITING_UNDERWRITING_APPROVAL)
    auth = svc.authorize(deal.deal_id, AuthorizationGate.UNDERWRITING, AuthorizationDecision.APPROVE,
                         "human", ActorType.HUMAN, "Proceed.")
    move(svc, deal.deal_id, WorkflowState.UNDERWRITING, auth=auth.authorization_id)
    with pytest.raises(WorkflowError, match="Illegal transition"):
        move(svc, deal.deal_id, WorkflowState.UNDERWRITING, auth=auth.authorization_id)


def test_investment_case_is_versionable_without_calculation_authority():
    from app.workflow import InvestmentCase

    case_v1 = InvestmentCase(deal_id="deal-1", version=1, assumptions=[{"type": "ASSUMPTION", "name": "rent_growth", "value": 0.04}])
    case_v2 = case_v1.model_copy(update={"version": 2, "assumptions": case_v1.assumptions + [{"type": "ASSUMPTION", "name": "vacancy", "value": 0.05}]})
    assert case_v1.version == 1
    assert case_v2.version == 2
    assert len(case_v1.assumptions) == 1
    assert len(case_v2.assumptions) == 2
