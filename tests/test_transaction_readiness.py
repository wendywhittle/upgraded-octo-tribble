from datetime import datetime, timezone

import pytest

from app.decision_gate import build_decision_gate
from app.institutional_lifecycle import InstitutionalLifecycle, LifecycleState
from app.transaction_readiness import (
    ReadinessItem,
    TransactionReadinessPackage,
    TransactionReadinessStatus,
)

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)


def _item(category, name, satisfied=True, required=True, source_refs=(), notes=""):
    return ReadinessItem(
        category=category,
        name=name,
        satisfied=satisfied,
        required=required,
        source_refs=source_refs,
        notes=notes,
    )


def _complete_package(**overrides):
    fields = {
        "proposed_terms": (_item("proposed_terms", "Purchase price and terms", source_refs=("E-TERM-1",)),),
        "capital_structure": (_item("capital_structure", "Debt and equity structure", source_refs=("E-FIN-1",)),),
        "diligence_requirements": (_item("diligence", "Diligence requirements satisfied", source_refs=("E-DIL-1",)),),
        "financing_conditions": (_item("financing", "Financing conditions satisfied", source_refs=("E-FIN-2",)),),
        "contractual_requirements": (_item("contractual", "Contract requirements identified", source_refs=("E-CON-1",)),),
        "required_approvals_signatures": (_item("approvals_signatures", "Required approvals identified"),),
        "responsible_parties": (_item("responsible_parties", "Responsible parties identified"),),
        "critical_dates": (_item("critical_dates", "Critical dates identified", notes="Target close: 2026-10-15"),),
        "unresolved_risks": (_item("risks", "Known risks recorded"),),
        "exceptions": (),
        "dependencies": (_item("dependencies", "Dependencies identified"),),
        "provenance_refs": ("E-TERM-1", "E-FIN-1", "E-DIL-1"),
        "audit_refs": ("decision:DR-001",),
    }
    fields.update(overrides)
    return TransactionReadinessPackage.create(
        "OPP-TRX-001",
        "OPP-TRX-001",
        "DR-001",
        **fields,
    )


def test_package_is_preparation_only_and_grants_no_authority():
    package = TransactionReadinessPackage.create("OPP-001", "OPP-001", "DR-001")

    assert package.has_investment_authority is False
    assert package.has_signature_authority is False
    assert package.has_execution_authority is False
    assert package.ready_for_signature is False


def test_missing_requirements_are_incomplete():
    package = _complete_package(
        financing_conditions=(_item("financing", "Lender condition", satisfied=False),)
    )

    assessed = package.assess(at=NOW)

    assert assessed.status is TransactionReadinessStatus.INCOMPLETE
    assert assessed.ready_for_signature is False
    assert assessed.has_execution_authority is False


def test_satisfied_package_can_reach_transaction_ready_status():
    package = _complete_package().assess(at=NOW)

    assert package.status is TransactionReadinessStatus.READY
    assert package.provenance_refs == ("E-TERM-1", "E-FIN-1", "E-DIL-1")
    assert package.audit_refs == ("decision:DR-001",)


def test_transaction_ready_does_not_promote_lifecycle_or_signature_authority():
    lifecycle = InstitutionalLifecycle.create("OPP-TRX-001").transition(
        LifecycleState.QUALIFIED, "qualified", at=NOW
    ).transition(
        LifecycleState.EVIDENCE_READY, "evidence ready", at=NOW
    ).transition(
        LifecycleState.DECISION_READY, "decision ready", at=NOW
    )
    package = _complete_package().assess(at=NOW)

    assert package.status is TransactionReadinessStatus.READY
    assert lifecycle.current_state is LifecycleState.DECISION_READY
    assert package.ready_for_signature is False
    assert package.has_investment_authority is False
    assert package.has_signature_authority is False
    assert package.has_execution_authority is False


def test_transaction_ready_does_not_become_human_authorized_or_executed():
    package = _complete_package().assess(at=NOW)

    assert package.status is TransactionReadinessStatus.READY
    assert package.has_investment_authority is False
    assert package.has_execution_authority is False
    assert package.ready_for_signature is False

    lifecycle = InstitutionalLifecycle.create(package.opportunity_id).transition(
        LifecycleState.QUALIFIED, "qualified", at=NOW
    ).transition(
        LifecycleState.EVIDENCE_READY, "evidence ready", at=NOW
    ).transition(
        LifecycleState.DECISION_READY, "decision ready", at=NOW
    ).transition(
        LifecycleState.TRANSACTION_READY, "transaction package ready", at=NOW
    )
    assert lifecycle.current_state is LifecycleState.TRANSACTION_READY
    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.HUMAN_AUTHORIZED, "automatic authorization")
    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.EXECUTED, "automatic execution")


def test_blocked_exception_is_not_transaction_ready():
    package = _complete_package(
        exceptions=(_item("exceptions", "Unresolved closing condition", satisfied=False),)
    ).assess(at=NOW)

    assert package.status is TransactionReadinessStatus.BLOCKED


def test_governance_and_decision_gate_behavior_remain_unchanged():
    governance = {
        "human_decision_required": True,
        "autonomous_execution": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "investment_authority": False,
    }
    gate = build_decision_gate(
        evidence={"count": 1, "usable_count": 1, "validation": [{"decision_usable": True}]},
        conflicts={"conflicts": [], "horizon_divergences": []},
        simulation={"valid": True},
        skeptic={"valid": True},
        synthesis={"verdict": "INVESTIGATE"},
        governance=governance,
    )
    before = dict(gate)
    package = _complete_package().assess(at=NOW)

    assert package.status is TransactionReadinessStatus.READY
    assert gate == before
    assert gate["state"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert gate["human_decision_required"] is True
    assert gate["autonomous_execution"] is False
    assert gate["brokerage_connectivity"] is False
    assert gate["portfolio_mutation"] is False
    assert gate["investment_authority"] is False


def test_identity_and_history_are_stable_and_immutable():
    package = _complete_package().assess(at=NOW)
    second = package.assess(at=NOW)

    assert package.opportunity_id == package.lifecycle_opportunity_id == "OPP-TRX-001"
    assert package.decision_record_id == "DR-001"
    assert len(package.history) == 1
    assert len(second.history) == 2
    assert package.history[0] == second.history[0]
    assert isinstance(package.history, tuple)
    with pytest.raises(Exception):
        package.history += ("mutation",)


def test_provider_neutral_contract_has_no_external_execution_fields_or_dependencies():
    package = _complete_package()

    assert package.status is TransactionReadinessStatus.NOT_READY
    assert not hasattr(package, "broker")
    assert not hasattr(package, "lender_api")
    assert not hasattr(package, "execute")
    assert not hasattr(package, "sign")
