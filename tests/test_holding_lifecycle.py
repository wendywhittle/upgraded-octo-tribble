from datetime import datetime, timezone

import pytest

from app.decision_gate import build_decision_gate
from app.holding_lifecycle import HoldingRecord, HoldingState
from app.human_authorization import HumanAuthorizationRecord, HumanAuthorizationStatus
from app.institutional_lifecycle import InstitutionalLifecycle, LifecycleState
from app.signature_readiness import SignatureReadinessPackage
from app.transaction_readiness import TransactionReadinessPackage

NOW = datetime(2026, 9, 13, 12, 0, tzinfo=timezone.utc)


def make_holding(**overrides):
    fields = {
        "opportunity_id": "OPP-HOLD-001",
        "lifecycle_opportunity_id": "OPP-HOLD-001",
        "decision_record_id": "DR-HOLD-001",
        "transaction_id": "TXN-HOLD-001",
        "human_authorization_id": "AUTH-HOLD-001",
        "asset_instrument_reference": "ASSET-001",
        "ownership_interest_reference": "OWNERSHIP-001",
        "acquisition_basis_reference": "BASIS-001",
        "capital_structure_references": ("CAP-001",),
        "provenance_references": ("PROV-001",),
        "audit_references": ("AUDIT-001",),
    }
    fields.update(overrides)
    return HoldingRecord.create(**fields)


def make_authorization():
    return HumanAuthorizationRecord.create(
        "OPP-HOLD-001", "OPP-HOLD-001", "DR-HOLD-001", "TXN-HOLD-001", "SIG-HOLD-001", "Acquire asset"
    ).submit_for_review(at=NOW).mark_human_reviewed(
        decision_maker_ref="HUMAN-001",
        authority_role_ref="ROLE-IC",
        reviewed_package_ref="SIG-HOLD-001",
        rationale="Reviewed package",
        at=NOW,
    ).record_human_decision(
        status=HumanAuthorizationStatus.AUTHORIZED,
        decision_maker_ref="HUMAN-001",
        authority_role_ref="ROLE-IC",
        reviewed_package_ref="SIG-HOLD-001",
        rationale="Explicit human authorization",
        at=NOW,
    )


def make_ready_gate():
    return build_decision_gate(
        evidence={"usable_count": 1, "validation": [{"decision_usable": True}]},
        conflicts={"conflicts": [], "horizon_divergences": []},
        simulation={"valid": True},
        skeptic={"valid": True},
        synthesis={"verdict": "INVESTIGATE"},
        governance={
            "autonomous_execution": False,
            "brokerage_connectivity": False,
            "portfolio_mutation": False,
            "investment_authority": False,
        },
    )


def test_holding_cannot_be_established_without_explicit_execution_fact():
    holding = make_holding()
    assert holding.state is HoldingState.EXECUTION_EVIDENCE_PENDING
    assert holding.established is False
    with pytest.raises(ValueError):
        holding.establish_from_execution_fact(execution_reference="", at=NOW)


def test_human_authorization_alone_does_not_create_holding():
    authorization = make_authorization()
    holding = make_holding()
    assert authorization.status is HumanAuthorizationStatus.AUTHORIZED
    assert holding.established is False


def test_signature_readiness_alone_does_not_create_holding():
    package = SignatureReadinessPackage.create(
        "TXN-HOLD-001", "OPP-HOLD-001", "OPP-HOLD-001", "DR-HOLD-001"
    )
    holding = make_holding()
    assert package.executed is False
    assert holding.established is False


def test_decision_gate_readiness_does_not_create_holding():
    gate = make_ready_gate()
    holding = make_holding()
    assert gate["state"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert holding.established is False


def test_explicit_execution_reference_establishes_holding_representation():
    holding = make_holding().establish_from_execution_fact(
        execution_reference="EXEC-2026-001",
        execution_provenance_refs=("EXEC-PROV-001",),
        acquisition_effective_date=NOW,
        at=NOW,
    )
    assert holding.state is HoldingState.HOLDING_ESTABLISHED
    assert holding.established is True
    assert holding.execution_reference == "EXEC-2026-001"
    assert holding.provenance_references == ("EXEC-PROV-001",)


def test_holding_identity_remains_stable():
    first = make_holding(holding_id="HOLD-STABLE-001")
    second = first.establish_from_execution_fact(execution_reference="EXEC-001", at=NOW)
    third = second.activate(at=NOW)
    assert first.holding_id == second.holding_id == third.holding_id == "HOLD-STABLE-001"


def test_all_institutional_identities_remain_traceable():
    holding = make_holding().establish_from_execution_fact(execution_reference="EXEC-001", at=NOW)
    assert holding.opportunity_id == "OPP-HOLD-001"
    assert holding.lifecycle_opportunity_id == "OPP-HOLD-001"
    assert holding.decision_record_id == "DR-HOLD-001"
    assert holding.transaction_id == "TXN-HOLD-001"
    assert holding.human_authorization_id == "AUTH-HOLD-001"
    assert holding.execution_reference == "EXEC-001"
    assert holding.asset_instrument_reference == "ASSET-001"
    assert holding.ownership_interest_reference == "OWNERSHIP-001"


def test_holding_history_is_immutable_and_append_only():
    first = make_holding()
    second = first.establish_from_execution_fact(execution_reference="EXEC-001", at=NOW)
    third = second.activate(at=NOW)
    assert isinstance(third.history, tuple)
    assert len(first.history) == 0
    assert len(second.history) == 1
    assert len(third.history) == 2
    assert third.history[:1] == second.history
    with pytest.raises(Exception):
        third.history += ()


def test_illegal_lifecycle_transitions_are_rejected():
    holding = make_holding()
    with pytest.raises(ValueError):
        holding.activate(at=NOW)
    with pytest.raises(ValueError):
        holding.mark_disposition_pending(at=NOW)
    active = holding.establish_from_execution_fact(execution_reference="EXEC-001", at=NOW).activate(at=NOW)
    with pytest.raises(ValueError):
        active.establish_from_execution_fact(execution_reference="EXEC-002", at=NOW)
    disposed = active.mark_disposition_pending(at=NOW).mark_disposed(at=NOW)
    with pytest.raises(ValueError):
        disposed.activate(at=NOW)


def test_holding_has_no_authority_or_action_capabilities():
    holding = make_holding().establish_from_execution_fact(execution_reference="EXEC-001", at=NOW)
    assert holding.has_investment_authority is False
    assert holding.has_execution_authority is False
    assert holding.has_signature_authority is False
    assert holding.funding_authority is False
    assert holding.closing_authority is False
    assert holding.brokerage_authority is False
    assert holding.portfolio_mutation_permitted is False
    assert holding.capital_transfer_permitted is False
    assert holding.signed is False
    assert holding.funded is False
    assert holding.closed is False
    assert holding.traded is False
    for name in ("execute", "sign", "fund", "close", "trade", "place_order", "transfer_capital", "connect_broker"):
        assert not hasattr(holding, name)


def test_missing_execution_provenance_remains_visible():
    holding = make_holding(provenance_references=())
    assert holding.state is HoldingState.EXECUTION_EVIDENCE_PENDING
    assert holding.execution_evidence_present is False
    assert holding.provenance_references == ()
    assert holding.established is False


def test_acquisition_date_is_represented_without_execution_capability():
    holding = make_holding(acquisition_effective_date=NOW)
    assert holding.acquisition_effective_date == NOW
    assert holding.established is False
    assert holding.has_execution_authority is False


def test_capital_structure_references_are_informational_only():
    holding = make_holding(capital_structure_references=("DEBT-001", "EQUITY-001"))
    assert holding.capital_structure_references == ("DEBT-001", "EQUITY-001")
    assert holding.funding_authority is False
    assert holding.capital_transfer_permitted is False


def test_holding_status_progression_is_explicit():
    holding = make_holding()
    assert holding.state is HoldingState.EXECUTION_EVIDENCE_PENDING
    established = holding.establish_from_execution_fact(execution_reference="EXEC-001", at=NOW)
    active = established.activate(at=NOW)
    pending = active.mark_disposition_pending(at=NOW)
    disposed = pending.mark_disposed(at=NOW)
    assert [entry.to_state for entry in disposed.history] == [
        HoldingState.HOLDING_ESTABLISHED,
        HoldingState.HOLDING_ACTIVE,
        HoldingState.DISPOSITION_PENDING,
        HoldingState.DISPOSED,
    ]


def test_existing_institutional_lifecycle_authority_protections_remain_intact():
    lifecycle = InstitutionalLifecycle.create("OPP-HOLD-001")
    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.HUMAN_AUTHORIZED, "automatic authorization", at=NOW)
    with pytest.raises(PermissionError):
        lifecycle.transition(LifecycleState.EXECUTED, "automatic execution", at=NOW)
    assert lifecycle.has_investment_authority is False
    assert lifecycle.has_execution_authority is False


def test_transaction_readiness_remains_preparation_only():
    package = TransactionReadinessPackage.create("OPP-HOLD-001", "OPP-HOLD-001", "DR-HOLD-001")
    assert package.ready_for_signature is False
    assert package.has_investment_authority is False
    assert package.has_execution_authority is False


def test_signature_readiness_remains_preparation_only():
    package = SignatureReadinessPackage.create("TXN-HOLD-001", "OPP-HOLD-001", "OPP-HOLD-001", "DR-HOLD-001")
    assert package.approved is False
    assert package.signed is False
    assert package.executed is False
    assert package.has_human_authorization is False


def test_human_authorization_remains_explicit():
    record = make_authorization()
    assert record.status is HumanAuthorizationStatus.AUTHORIZED
    assert record.executed is False
    assert record.signed is False
    assert record.closed is False
    assert record.funded is False
    assert record.capital_transfer_permitted is False
    assert record.portfolio_mutation_permitted is False


def test_decision_gate_remains_readiness_only():
    gate = make_ready_gate()
    assert gate["state"] == "OPEN_READY_FOR_HUMAN_AUTHORITY"
    assert gate["ready_for_human_authority"] is True
    assert gate["human_authorization"] is None
    assert gate["autonomous_execution"] is False
    assert gate["brokerage_connectivity"] is False
    assert gate["portfolio_mutation"] is False
    assert gate["investment_authority"] is False


def test_no_provider_persistence_or_external_execution_dependency():
    holding = make_holding()
    assert not hasattr(holding, "broker")
    assert not hasattr(holding, "provider")
    assert not hasattr(holding, "database")
    assert not hasattr(holding, "save")
    assert not hasattr(holding, "execute")


def test_execution_reference_is_required_even_when_authorization_exists():
    record = make_authorization()
    holding = make_holding(human_authorization_id=record.authorization_id)
    assert record.status is HumanAuthorizationStatus.AUTHORIZED
    assert holding.state is HoldingState.EXECUTION_EVIDENCE_PENDING
    assert holding.established is False


def test_readiness_states_never_establish_holding():
    gate = make_ready_gate()
    tx = TransactionReadinessPackage.create("OPP-HOLD-001", "OPP-HOLD-001", "DR-HOLD-001")
    sig = SignatureReadinessPackage.create("TXN-HOLD-001", "OPP-HOLD-001", "OPP-HOLD-001", "DR-HOLD-001")
    holding = make_holding()
    assert gate["ready_for_human_authority"] is True
    assert tx.status.value == "NOT_READY"
    assert sig.status.value == "NOT_READY"
    assert holding.established is False


def test_establishment_does_not_imply_approval_authorization_signing_or_execution_authority():
    holding = make_holding().establish_from_execution_fact(execution_reference="EXEC-001", at=NOW)
    assert holding.established is True
    assert holding.has_investment_authority is False
    assert holding.has_execution_authority is False
    assert holding.has_signature_authority is False
    assert holding.signed is False
    assert holding.funded is False
    assert holding.closed is False


def test_external_execution_fact_is_represented_not_verified_or_performed():
    holding = make_holding().establish_from_execution_fact(
        execution_reference="EXTERNAL-EXEC-FACT-001",
        execution_provenance_refs=("EXTERNAL-SOURCE-001",),
        at=NOW,
    )
    assert holding.execution_reference == "EXTERNAL-EXEC-FACT-001"
    assert holding.provenance_references == ("EXTERNAL-SOURCE-001",)
    assert holding.has_execution_authority is False


def test_disposition_states_are_only_lifecycle_representation():
    holding = make_holding().establish_from_execution_fact(execution_reference="EXEC-001", at=NOW).activate(at=NOW)
    pending = holding.mark_disposition_pending(at=NOW)
    disposed = pending.mark_disposed(at=NOW)
    assert pending.state is HoldingState.DISPOSITION_PENDING
    assert disposed.state is HoldingState.DISPOSED
    assert not hasattr(holding, "execute_disposition")
    assert not hasattr(holding, "settle")


def test_identity_fields_are_nonempty():
    for field_name in (
        "opportunity_id",
        "lifecycle_opportunity_id",
        "decision_record_id",
        "transaction_id",
        "human_authorization_id",
    ):
        with pytest.raises(ValueError):
            fields = {
                "opportunity_id": "OPP-HOLD-001",
                "lifecycle_opportunity_id": "OPP-HOLD-001",
                "decision_record_id": "DR-HOLD-001",
                "transaction_id": "TXN-HOLD-001",
                "human_authorization_id": "AUTH-HOLD-001",
            }
            fields[field_name] = ""
            HoldingRecord.create(**fields)


def test_execution_reference_remains_stable_through_lifecycle():
    holding = make_holding().establish_from_execution_fact(execution_reference="EXEC-STABLE", at=NOW)
    active = holding.activate(at=NOW)
    pending = active.mark_disposition_pending(at=NOW)
    disposed = pending.mark_disposed(at=NOW)
    assert all(item.execution_reference == "EXEC-STABLE" for item in (holding, active, pending, disposed))
