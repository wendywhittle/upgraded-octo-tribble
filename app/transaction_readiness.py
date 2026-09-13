"""Provider-neutral transaction readiness boundary.

This module represents preparation status between analytical decision readiness
and future signature preparation. It does not execute transactions, grant
investment or signature authority, sign documents, move capital, or persist data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import FrozenSet, Optional, Tuple
from uuid import uuid4


class TransactionReadinessStatus(str, Enum):
    NOT_READY = "NOT_READY"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"
    CONDITIONAL = "CONDITIONAL"
    READY = "READY"


@dataclass(frozen=True)
class ReadinessItem:
    """Immutable transaction-preparation requirement."""

    category: str
    name: str
    satisfied: bool
    required: bool = True
    source_refs: Tuple[str, ...] = ()
    notes: str = ""

    def __post_init__(self) -> None:
        if not self.category.strip() or not self.name.strip():
            raise ValueError("category and name must be non-empty")


@dataclass(frozen=True)
class TransactionReadinessPackage:
    """Immutable, provider-neutral transaction readiness snapshot."""

    transaction_id: str
    opportunity_id: str
    lifecycle_opportunity_id: str
    decision_record_id: str
    proposed_terms: Tuple[ReadinessItem, ...] = ()
    capital_structure: Tuple[ReadinessItem, ...] = ()
    diligence_requirements: Tuple[ReadinessItem, ...] = ()
    financing_conditions: Tuple[ReadinessItem, ...] = ()
    contractual_requirements: Tuple[ReadinessItem, ...] = ()
    required_approvals_signatures: Tuple[ReadinessItem, ...] = ()
    responsible_parties: Tuple[ReadinessItem, ...] = ()
    critical_dates: Tuple[ReadinessItem, ...] = ()
    unresolved_risks: Tuple[ReadinessItem, ...] = ()
    exceptions: Tuple[ReadinessItem, ...] = ()
    dependencies: Tuple[ReadinessItem, ...] = ()
    provenance_refs: Tuple[str, ...] = ()
    audit_refs: Tuple[str, ...] = ()
    status: TransactionReadinessStatus = TransactionReadinessStatus.NOT_READY
    assessed_at: Optional[datetime] = None
    history: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        opportunity_id: str,
        lifecycle_opportunity_id: str,
        decision_record_id: str,
        *,
        transaction_id: Optional[str] = None,
        **kwargs,
    ) -> "TransactionReadinessPackage":
        """Create a preparation package without changing lifecycle authority."""
        for name, value in {
            "opportunity_id": opportunity_id,
            "lifecycle_opportunity_id": lifecycle_opportunity_id,
            "decision_record_id": decision_record_id,
        }.items():
            if not value.strip():
                raise ValueError(f"{name} must be non-empty")
        return cls(
            transaction_id=transaction_id or f"TXN-{uuid4().hex[:16]}",
            opportunity_id=opportunity_id,
            lifecycle_opportunity_id=lifecycle_opportunity_id,
            decision_record_id=decision_record_id,
            **kwargs,
        )

    @property
    def has_investment_authority(self) -> bool:
        return False

    @property
    def has_signature_authority(self) -> bool:
        return False

    @property
    def has_execution_authority(self) -> bool:
        return False

    @property
    def ready_for_signature(self) -> bool:
        return False

    def assess(self, *, at: Optional[datetime] = None) -> "TransactionReadinessPackage":
        """Assess preparation completeness without promoting any lifecycle state."""
        items = self._all_items()
        required = [item for item in items if item.required]
        unsatisfied = [item for item in required if not item.satisfied]
        exception_blockers = [item for item in self.exceptions if item.required and not item.satisfied]

        if not items:
            status = TransactionReadinessStatus.NOT_READY
        elif exception_blockers:
            status = TransactionReadinessStatus.BLOCKED
        elif unsatisfied:
            status = TransactionReadinessStatus.INCOMPLETE
        elif any(item for item in self.exceptions if not item.satisfied):
            status = TransactionReadinessStatus.CONDITIONAL
        else:
            status = TransactionReadinessStatus.READY

        timestamp = at or datetime.now(timezone.utc)
        history_entry = f"{timestamp.isoformat()}:{status.value}"
        return TransactionReadinessPackage(
            transaction_id=self.transaction_id,
            opportunity_id=self.opportunity_id,
            lifecycle_opportunity_id=self.lifecycle_opportunity_id,
            decision_record_id=self.decision_record_id,
            proposed_terms=self.proposed_terms,
            capital_structure=self.capital_structure,
            diligence_requirements=self.diligence_requirements,
            financing_conditions=self.financing_conditions,
            contractual_requirements=self.contractual_requirements,
            required_approvals_signatures=self.required_approvals_signatures,
            responsible_parties=self.responsible_parties,
            critical_dates=self.critical_dates,
            unresolved_risks=self.unresolved_risks,
            exceptions=self.exceptions,
            dependencies=self.dependencies,
            provenance_refs=self.provenance_refs,
            audit_refs=self.audit_refs,
            status=status,
            assessed_at=timestamp,
            history=self.history + (history_entry,),
        )

    def _all_items(self) -> Tuple[ReadinessItem, ...]:
        return (
            self.proposed_terms
            + self.capital_structure
            + self.diligence_requirements
            + self.financing_conditions
            + self.contractual_requirements
            + self.required_approvals_signatures
            + self.responsible_parties
            + self.critical_dates
            + self.unresolved_risks
            + self.exceptions
            + self.dependencies
        )


def required_categories() -> FrozenSet[str]:
    """Categories available to a transaction package without vendor assumptions."""
    return frozenset({
        "proposed_terms",
        "capital_structure",
        "diligence",
        "financing",
        "contractual",
        "approvals_signatures",
        "responsible_parties",
        "critical_dates",
        "risks",
        "exceptions",
        "dependencies",
    })
