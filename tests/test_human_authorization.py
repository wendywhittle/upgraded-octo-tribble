from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from app.human_authorization import (
    HumanAuthorizationRecord,
    HumanAuthorizationStatus,
)
from app.institutional_lifecycle import InstitutionalLifecycle, LifecycleState
from app.signature_readiness import SignatureReadinessStatus
from app.transaction_readiness import TransactionReadinessStatus


AT = datetime(2026, 1, 2, tzinfo=timezone.utc)


def record():
    return HumanAuthorizationRecord.create(
        "OPP-1", "OPP-1", "DEC-1", "TXN-1", "SIG-1", "Acquire asset"
    )


def reviewed():
    return record().submit_for_review(at=AT).mark_human_reviewed(
        decision_maker_ref="human-1",
        authority_role_ref="investment-authority",
        reviewed_package_ref="SIG-1",
        rationale="Reviewed prepared package and evidence.",
        at=AT,
    )


def test_record_can_await_human_review_without_authority():
    p = record().submit_for_review(at=AT)
    assert p.status is HumanAuthorizationStatus.AWAITING_HUMAN_REVIEW
    assert p.has_investment_authority is False
    assert p.has_signature_authority is False
    assert p.has_execution_authority is False


def test_signature_readiness_does_not_auto_authorize():
    assert SignatureReadinessStatus.READY_FOR_HUMAN_SIGNATURE.value != HumanAuthorizationStatus.AUTHORIZED.value
    assert record().status is HumanAuthorizationStatus.NOT_SUBMITTED


def test_system_recommendation_cannot_create_authorization_event():
    p = record()
    assert not hasattr(p, "auto_authorize")
    assert not hasattr(p, "authorize_if_ready")
    assert p.events == ()


def test_decision_gate_readiness_does_not_auto_authorize():
    p = record()
    decision_gate = {"state": "OPEN_READY_FOR_HUMAN_AUTHORITY"}
    assert decision_gate["state"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert p.status is HumanAuthorizationStatus.NOT_SUBMITTED
    assert p.events == ()


def test_explicit_human_information_is_required():
    with pytest.raises(ValueError):
        reviewed().record_human_decision(
            status=HumanAuthorizationStatus.AUTHORIZED,
            decision_maker_ref="",
            authority_role_ref="investment-authority",
            reviewed_package_ref="SIG-1",
            rationale="Approved.",
            at=AT,
        )


def test_explicit_human_authorization_can_be_recorded():
    p = reviewed().record_human_decision(
        status=HumanAuthorizationStatus.AUTHORIZED,
        decision_maker_ref="human-1",
        authority_role_ref="investment-authority",
        reviewed_package_ref="SIG-1",
        rationale="Explicit human authorization after review.",
        at=AT,
    )
    assert p.status is HumanAuthorizationStatus.AUTHORIZED
    assert len(p.events) == 2
    assert p.events[-1].status is HumanAuthorizationStatus.AUTHORIZED
    assert p.events[-1].decision_maker_ref == "human-1"
    assert p.events[-1].authority_role_ref == "investment-authority"


def test_conditional_authorization_preserves_conditions():
    p = reviewed().record_human_decision(
        status=HumanAuthorizationStatus.CONDITIONAL_AUTHORIZATION,
        decision_maker_ref="human-1",
        authority_role_ref="investment-authority",
        reviewed_package_ref="SIG-1",
        rationale="Authorize subject to named conditions.",
        conditions=("final financing condition", "title diligence complete"),
        at=AT,
    )
    assert p.status is HumanAuthorizationStatus.CONDITIONAL_AUTHORIZATION
    assert p.events[-1].conditions == ("final financing condition", "title diligence complete")


def test_conditional_authorization_requires_named_conditions():
    with pytest.raises(ValueError):
        reviewed().record_human_decision(
            status=HumanAuthorizationStatus.CONDITIONAL_AUTHORIZATION,
            decision_maker_ref="human-1",
            authority_role_ref="investment-authority",
            reviewed_package_ref="SIG-1",
            rationale="Conditional.",
            at=AT,
        )


def test_rejected_is_legitimate_human_outcome():
    p = reviewed().record_human_decision(
        status=HumanAuthorizationStatus.REJECTED,
        decision_maker_ref="human-1",
        authority_role_ref="investment-authority",
        reviewed_package_ref="SIG-1",
        rationale="Material risk not accepted.",
        at=AT,
    )
    assert p.status is HumanAuthorizationStatus.REJECTED


def test_withdrawal_preserves_prior_authorization_history():
    authorized = reviewed().record_human_decision(
        status=HumanAuthorizationStatus.AUTHORIZED,
        decision_maker_ref="human-1",
        authority_role_ref="investment-authority",
        reviewed_package_ref="SIG-1",
        rationale="Explicit authorization.",
        at=AT,
    )
    withdrawn = authorized.withdraw(at=AT, rationale="Authorization withdrawn pending new information.")
    assert withdrawn.status is HumanAuthorizationStatus.WITHDRAWN
    assert len(withdrawn.events) == 3
    assert withdrawn.events[1].status is HumanAuthorizationStatus.AUTHORIZED
    assert withdrawn.events[2].status is HumanAuthorizationStatus.WITHDRAWN


def test_authorization_is_not_execution_or_signature():
    p = reviewed().record_human_decision(
        status=HumanAuthorizationStatus.AUTHORIZED,
        decision_maker_ref="human-1",
        authority_role_ref="investment-authority",
        reviewed_package_ref="SIG-1",
        rationale="Authorized.",
        at=AT,
    )
    assert p.signed is False
    assert p.executed is False
    assert p.closed is False
    assert p.funded is False
    assert p.has_signature_authority is False
    assert p.has_execution_authority is False


def test_authorization_has_no_execution_capability():
    p = reviewed().record_human_decision(
        status=HumanAuthorizationStatus.AUTHORIZED,
        decision_maker_ref="human-1",
        authority_role_ref="investment-authority",
        reviewed_package_ref="SIG-1",
        rationale="Authorized.",
        at=AT,
    )
    assert not hasattr(p, "execute")
    assert not hasattr(p, "sign")
    assert not hasattr(p, "fund")
    assert not hasattr(p, "close")
    assert p.portfolio_mutation_permitted is False
    assert p.capital_transfer_permitted is False


def test_lifecycle_authority_protections_remain_intact():
    lifecycle = InstitutionalLifecycle.create("OPP-1")
    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.HUMAN_AUTHORIZED, "test")
    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.EXECUTED, "test")


def test_existing_readiness_contracts_remain_separate():
    assert TransactionReadinessStatus.READY.value != HumanAuthorizationStatus.AUTHORIZED.value
    assert SignatureReadinessStatus.READY_FOR_HUMAN_SIGNATURE.value != HumanAuthorizationStatus.AUTHORIZED.value


def test_identity_relationships_are_stable():
    p = record()
    assert p.authorization_id.startswith("AUTH-")
    assert p.opportunity_id == "OPP-1"
    assert p.lifecycle_opportunity_id == "OPP-1"
    assert p.decision_record_id == "DEC-1"
    assert p.transaction_readiness_id == "TXN-1"
    assert p.signature_readiness_id == "SIG-1"


def test_evidence_risk_exception_and_audit_references_are_preserved():
    p = HumanAuthorizationRecord.create(
        "OPP-1", "OPP-1", "DEC-1", "TXN-1", "SIG-1", "Acquire asset",
        reviewed_evidence_refs=("E-1",),
        reviewed_risk_refs=("R-1",),
        reviewed_exception_refs=("X-1",),
        reviewed_condition_refs=("C-1",),
        required_conditions_precedent=("CP-1",),
        critical_deadlines=("2026-02-01",),
        audit_refs=("AUD-1",),
    )
    assert p.reviewed_evidence_refs == ("E-1",)
    assert p.reviewed_risk_refs == ("R-1",)
    assert p.reviewed_exception_refs == ("X-1",)
    assert p.reviewed_condition_refs == ("C-1",)
    assert p.required_conditions_precedent == ("CP-1",)
    assert p.critical_deadlines == ("2026-02-01",)
    assert p.audit_refs == ("AUD-1",)


def test_history_is_immutable_and_append_only():
    p = reviewed()
    authorized = p.record_human_decision(
        status=HumanAuthorizationStatus.AUTHORIZED,
        decision_maker_ref="human-1",
        authority_role_ref="investment-authority",
        reviewed_package_ref="SIG-1",
        rationale="Authorized.",
        at=AT,
    )
    assert len(p.events) == 1
    assert len(authorized.events) == 2
    assert authorized.events[0] == p.events[0]
    with pytest.raises(FrozenInstanceError):
        p.status = HumanAuthorizationStatus.AUTHORIZED


def test_no_sensitive_authentication_material_is_required():
    p = record().submit_for_review(at=AT)
    assert not hasattr(p, "password")
    assert not hasattr(p, "credential")
    assert not hasattr(p, "identity_document")


def test_provider_neutral_contract():
    p = record()
    assert not hasattr(p, "esign_provider")
    assert not hasattr(p, "broker_api")
    assert not hasattr(p, "banking_api")
    assert not hasattr(p, "lender_api")
