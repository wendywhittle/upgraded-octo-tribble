"""Provider-neutral holding and ownership lifecycle boundary.

This module represents a holding established by an explicit external execution
fact. It does not execute, authorize, sign, fund, close, trade, broker, move
capital, mutate portfolios, persist data, or verify external execution.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Tuple
from uuid import uuid4


class HoldingState(str, Enum):
    PROPOSED = "PROPOSED"
    EXECUTION_EVIDENCE_PENDING = "EXECUTION_EVIDENCE_PENDING"
    HOLDING_ESTABLISHED = "HOLDING_ESTABLISHED"
    HOLDING_ACTIVE = "HOLDING_ACTIVE"
    DISPOSITION_PENDING = "DISPOSITION_PENDING"
    DISPOSED = "DISPOSED"


@dataclass(frozen=True)
class HoldingTransition:
    """Immutable historical holding-state transition."""

    from_state: HoldingState
    to_state: HoldingState
    at: datetime
    reason: str


@dataclass(frozen=True)
class HoldingRecord:
    """Immutable representation of an externally established holding."""

    holding_id: str
    opportunity_id: str
    lifecycle_opportunity_id: str
    decision_record_id: str
    transaction_id: str
    human_authorization_id: str
    execution_reference: Optional[str] = None
    asset_instrument_reference: str = ""
    ownership_interest_reference: str = ""
    acquisition_effective_date: Optional[datetime] = None
    acquisition_basis_reference: Optional[str] = None
    capital_structure_references: Tuple[str, ...] = ()
    provenance_references: Tuple[str, ...] = ()
    audit_references: Tuple[str, ...] = ()
    state: HoldingState = HoldingState.PROPOSED
    operating_status: str = "NOT_ESTABLISHED"
    financing_status: str = "NOT_ESTABLISHED"
    improvement_status: str = "NOT_ESTABLISHED"
    history: Tuple[HoldingTransition, ...] = field(default_factory=tuple)

    @classmethod
    def create(cls, opportunity_id: str, lifecycle_opportunity_id: str, decision_record_id: str,
               transaction_id: str, human_authorization_id: str, *, holding_id: Optional[str] = None,
               execution_reference: Optional[str] = None, asset_instrument_reference: str = "",
               ownership_interest_reference: str = "", acquisition_effective_date: Optional[datetime] = None,
               acquisition_basis_reference: Optional[str] = None, capital_structure_references: Tuple[str, ...] = (),
               provenance_references: Tuple[str, ...] = (), audit_references: Tuple[str, ...] = (),
               operating_status: str = "NOT_ESTABLISHED", financing_status: str = "NOT_ESTABLISHED",
               improvement_status: str = "NOT_ESTABLISHED") -> "HoldingRecord":
        """Create a holding representation without inferring execution."""
        for name, value in {"opportunity_id": opportunity_id, "lifecycle_opportunity_id": lifecycle_opportunity_id,
                             "decision_record_id": decision_record_id, "transaction_id": transaction_id,
                             "human_authorization_id": human_authorization_id}.items():
            if not isinstance(value, str) or not value.strip():
                raise ValueError(f"{name} must be non-empty")
        return cls(
            holding_id=holding_id or f"HOLD-{uuid4().hex[:16]}", opportunity_id=opportunity_id,
            lifecycle_opportunity_id=lifecycle_opportunity_id, decision_record_id=decision_record_id,
            transaction_id=transaction_id, human_authorization_id=human_authorization_id,
            execution_reference=execution_reference, asset_instrument_reference=asset_instrument_reference,
            ownership_interest_reference=ownership_interest_reference, acquisition_effective_date=acquisition_effective_date,
            acquisition_basis_reference=acquisition_basis_reference, capital_structure_references=tuple(capital_structure_references),
            provenance_references=tuple(provenance_references), audit_references=tuple(audit_references),
            state=(HoldingState.EXECUTION_EVIDENCE_PENDING if not execution_reference or not execution_reference.strip()
                   else HoldingState.PROPOSED), operating_status=operating_status,
            financing_status=financing_status, improvement_status=improvement_status,
        )

    @property
    def execution_evidence_present(self) -> bool:
        return bool(self.execution_reference and self.execution_reference.strip())

    @property
    def established(self) -> bool:
        return self.state in {HoldingState.HOLDING_ESTABLISHED, HoldingState.HOLDING_ACTIVE,
                               HoldingState.DISPOSITION_PENDING, HoldingState.DISPOSED}

    @property
    def has_investment_authority(self) -> bool: return False
    @property
    def has_execution_authority(self) -> bool: return False
    @property
    def has_signature_authority(self) -> bool: return False
    @property
    def funding_authority(self) -> bool: return False
    @property
    def closing_authority(self) -> bool: return False
    @property
    def brokerage_authority(self) -> bool: return False
    @property
    def portfolio_mutation_permitted(self) -> bool: return False
    @property
    def capital_transfer_permitted(self) -> bool: return False
    @property
    def signed(self) -> bool: return False
    @property
    def funded(self) -> bool: return False
    @property
    def closed(self) -> bool: return False
    @property
    def traded(self) -> bool: return False

    def mark_execution_evidence_pending(self, *, reason: str = "Execution evidence pending",
                                        at: Optional[datetime] = None) -> "HoldingRecord":
        return self._transition(HoldingState.EXECUTION_EVIDENCE_PENDING, reason, at=at)

    def establish_from_execution_fact(self, *, execution_reference: str,
                                      execution_provenance_refs: Tuple[str, ...] = (),
                                      acquisition_effective_date: Optional[datetime] = None,
                                      reason: str = "Explicit external execution fact supplied",
                                      at: Optional[datetime] = None) -> "HoldingRecord":
        """Represent an externally supplied execution fact as a holding.

        This method records supplied evidence only. It does not perform or
        independently verify execution and never grants authority.
        """
        if not isinstance(execution_reference, str) or not execution_reference.strip():
            raise ValueError("execution_reference must be non-empty")
        if self.state not in {HoldingState.PROPOSED, HoldingState.EXECUTION_EVIDENCE_PENDING}:
            raise ValueError(f"Cannot establish from {self.state.value}")
        provenance = tuple(execution_provenance_refs) or self.provenance_references
        timestamp = at or datetime.now(timezone.utc)
        data = self._data_without_history()
        data.update({"execution_reference": execution_reference,
                     "acquisition_effective_date": acquisition_effective_date or self.acquisition_effective_date,
                     "provenance_references": provenance, "state": HoldingState.HOLDING_ESTABLISHED,
                     "operating_status": "ESTABLISHED",
                     "history": self.history + (HoldingTransition(self.state, HoldingState.HOLDING_ESTABLISHED, timestamp, reason),)})
        return HoldingRecord(**data)

    def activate(self, *, reason: str = "Holding activated", at: Optional[datetime] = None) -> "HoldingRecord":
        return self._transition(HoldingState.HOLDING_ACTIVE, reason, at=at)

    def mark_disposition_pending(self, *, reason: str = "Disposition pending",
                                 at: Optional[datetime] = None) -> "HoldingRecord":
        return self._transition(HoldingState.DISPOSITION_PENDING, reason, at=at)

    def mark_disposed(self, *, reason: str = "Holding disposed", at: Optional[datetime] = None) -> "HoldingRecord":
        return self._transition(HoldingState.DISPOSED, reason, at=at)

    def _transition(self, to_state: HoldingState, reason: str, *, at: Optional[datetime]) -> "HoldingRecord":
        if not isinstance(to_state, HoldingState): raise TypeError("to_state must be a HoldingState")
        if not isinstance(reason, str) or not reason.strip(): raise ValueError("reason must be non-empty")
        allowed = {
            HoldingState.PROPOSED: {HoldingState.EXECUTION_EVIDENCE_PENDING},
            HoldingState.EXECUTION_EVIDENCE_PENDING: {HoldingState.HOLDING_ESTABLISHED},
            HoldingState.HOLDING_ESTABLISHED: {HoldingState.HOLDING_ACTIVE},
            HoldingState.HOLDING_ACTIVE: {HoldingState.DISPOSITION_PENDING},
            HoldingState.DISPOSITION_PENDING: {HoldingState.DISPOSED},
            HoldingState.DISPOSED: set(),
        }
        if to_state not in allowed[self.state]:
            raise ValueError(f"Illegal holding transition: {self.state.value} -> {to_state.value}")
        timestamp = at or datetime.now(timezone.utc)
        data = self._data_without_history()
        data.update({"state": to_state,
                     "operating_status": "ACTIVE" if to_state is HoldingState.HOLDING_ACTIVE else self.operating_status,
                     "history": self.history + (HoldingTransition(self.state, to_state, timestamp, reason),)})
        return HoldingRecord(**data)

    def _data_without_history(self) -> dict:
        return {
            "holding_id": self.holding_id, "opportunity_id": self.opportunity_id,
            "lifecycle_opportunity_id": self.lifecycle_opportunity_id, "decision_record_id": self.decision_record_id,
            "transaction_id": self.transaction_id, "human_authorization_id": self.human_authorization_id,
            "execution_reference": self.execution_reference, "asset_instrument_reference": self.asset_instrument_reference,
            "ownership_interest_reference": self.ownership_interest_reference,
            "acquisition_effective_date": self.acquisition_effective_date,
            "acquisition_basis_reference": self.acquisition_basis_reference,
            "capital_structure_references": self.capital_structure_references,
            "provenance_references": self.provenance_references, "audit_references": self.audit_references,
            "financing_status": self.financing_status, "improvement_status": self.improvement_status,
        }
