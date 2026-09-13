from dataclasses import FrozenInstanceError
from datetime import datetime, timezone

import pytest

from app.institutional_lifecycle import InstitutionalLifecycle, LifecycleState
from app.signature_readiness import (
    SignatureReadinessItem,
    SignatureReadinessPackage,
    SignatureReadinessStatus,
)
from app.transaction_readiness import TransactionReadinessPackage, TransactionReadinessStatus


AT = datetime(2026, 1, 1, tzinfo=timezone.utc)


def item(category="diligence", name="item", satisfied=True, required=True):
    return SignatureReadinessItem(category, name, satisfied, required)


def package(**kwargs):
    return SignatureReadinessPackage.create(
        "TXN-1", "OPP-1", "OPP-1", "DEC-1", **kwargs
    )


def complete_package(**kwargs):
    return package(
        transaction_terms_refs=("terms-1",),
        capital_structure_refs=("capital-1",),
        diligence_status=(item(),),
        financing_conditions=(item("financing", "condition"),),
        contractual_requirements=(item("contractual", "document"),),
        required_approvals=(item("approval", "IC approval"),),
        required_signatures=(item("signature", "human signature"),),
        responsible_parties=(item("party", "responsible party"),),
        critical_dates=(item("date", "critical date"),),
        dependencies=(item("dependency", "dependency"),),
        required_human_decisions=(item("decision", "human decision"),),
        provenance_refs=("evidence-1",),
        audit_refs=("audit-1",),
        **kwargs,
    )


def test_creation_grants_no_authority():
    p = package()
    assert p.has_investment_authority is False
    assert p.has_human_authorization is False
    assert p.has_signature_authority is False
    assert p.has_execution_authority is False
    assert p.approved is False
    assert p.signed is False
    assert p.executed is False


def test_missing_conditions_are_incomplete():
    p = package(diligence_status=(item(satisfied=False),)).assess(at=AT)
    assert p.status is SignatureReadinessStatus.INCOMPLETE
    assert "INCOMPLETE" in p.history[-1]


def test_blocking_exception_is_blocked():
    p = complete_package(exceptions=(item("exception", "material blocker", False),)).assess(at=AT)
    assert p.status is SignatureReadinessStatus.BLOCKED


def test_nonblocking_exception_is_conditional():
    p = complete_package(exceptions=(item("exception", "accepted condition", False, False),)).assess(at=AT)
    assert p.status is SignatureReadinessStatus.CONDITIONAL


def test_complete_package_reaches_ready_for_human_signature():
    p = complete_package().assess(at=AT)
    assert p.status is SignatureReadinessStatus.READY_FOR_HUMAN_SIGNATURE
    assert p.approved is False
    assert p.has_human_authorization is False
    assert p.has_signature_authority is False
    assert p.has_execution_authority is False


def test_signature_readiness_has_no_execution_capability():
    p = complete_package().assess(at=AT)
    assert not hasattr(p, "execute")
    assert not hasattr(p, "sign")
    assert not hasattr(p, "close")
    assert not hasattr(p, "fund")
    assert not hasattr(p, "authorize")


def test_signature_ready_does_not_promote_lifecycle():
    p = complete_package().assess(at=AT)
    lifecycle = InstitutionalLifecycle.create("OPP-1")
    assert p.status is SignatureReadinessStatus.READY_FOR_HUMAN_SIGNATURE
    assert lifecycle.current_state is LifecycleState.DISCOVERED
    assert p.has_human_authorization is False


def test_existing_lifecycle_authority_protections_remain_intact():
    lifecycle = InstitutionalLifecycle.create("OPP-1")
    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.HUMAN_AUTHORIZED, "test")
    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.EXECUTED, "test")


def test_transaction_readiness_contract_remains_separate():
    txn = TransactionReadinessPackage.create("OPP-1", "OPP-1", "DEC-1")
    assert txn.status is TransactionReadinessStatus.NOT_READY
    assert txn.has_investment_authority is False
    assert txn.has_signature_authority is False
    assert txn.has_execution_authority is False


def test_stable_identity_relationships():
    p = complete_package().assess(at=AT)
    assert p.signature_package_id.startswith("SIG-")
    assert p.transaction_readiness_id == "TXN-1"
    assert p.opportunity_id == "OPP-1"
    assert p.lifecycle_opportunity_id == "OPP-1"
    assert p.decision_record_id == "DEC-1"


def test_history_is_append_only_and_immutable():
    first = complete_package().assess(at=AT)
    second = first.assess(at=AT)
    assert len(first.history) == 1
    assert len(second.history) == 2
    assert second.history[0] == first.history[0]
    with pytest.raises(FrozenInstanceError):
        first.status = SignatureReadinessStatus.READY_FOR_HUMAN_SIGNATURE


def test_provenance_and_audit_references_are_preserved():
    p = complete_package().assess(at=AT)
    assert p.provenance_refs == ("evidence-1",)
    assert p.audit_refs == ("audit-1",)


def test_provider_neutral_contract_has_no_provider_fields():
    p = package()
    assert not hasattr(p, "broker_api")
    assert not hasattr(p, "lender_api")
    assert not hasattr(p, "esign_provider")
    assert not hasattr(p, "banking_api")


def test_empty_package_is_not_ready():
    assert package().assess(at=AT).status is SignatureReadinessStatus.NOT_READY


def test_required_human_signature_remains_a_requirement_not_an_authorization():
    p = complete_package(
        required_signatures=(item("signature", "human signature", satisfied=False),)
    ).assess(at=AT)
    assert p.status is SignatureReadinessStatus.INCOMPLETE
    assert p.has_signature_authority is False


def test_explicit_missing_provenance_can_be_represented():
    p = complete_package(
        diligence_status=(item("diligence", "source provenance", False),)
    ).assess(at=AT)
    assert p.status is SignatureReadinessStatus.INCOMPLETE


def test_ready_is_not_a_lifecycle_state_transition():
    lifecycle = InstitutionalLifecycle.create("OPP-1")
    ready = complete_package().assess(at=AT)
    assert ready.status.value == "READY_FOR_HUMAN_SIGNATURE"
    assert lifecycle.current_state is LifecycleState.DISCOVERED
