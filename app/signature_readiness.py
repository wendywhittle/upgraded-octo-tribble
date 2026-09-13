"""Provider-neutral signature readiness boundary.

This module represents whether a transaction package is prepared for human
review and potential signature. It does not approve, authorize, sign, execute,
close, fund, negotiate, or persist transactions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Tuple
from uuid import uuid4


class SignatureReadinessStatus(str, Enum):
    NOT_READY = "NOT_READY"
    INCOMPLETE = "INCOMPLETE"
    BLOCKED = "BLOCKED"
    CONDITIONAL = "CONDITIONAL"
    READY_FOR_HUMAN_SIGNATURE = "READY_FOR_HUMAN_SIGNATURE"


@dataclass(frozen=True)
class SignatureReadinessItem:
    """Immutable signature-preparation requirement."""

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
class SignatureReadinessPackage:
    """Immutable, provider-neutral signature readiness snapshot."""

    signature_package_id: str
    transaction_readiness_id: str
    opportunity_id: str
    lifecycle_opportunity_id: str
    decision_record_id: str
    transaction_terms_refs: Tuple[str, ...] = ()
    capital_structure_refs: Tuple[str, ...] = ()
    diligence_status: Tuple[SignatureReadinessItem, ...] = ()
    financing_conditions: Tuple[SignatureReadinessItem, ...] = ()
    contractual_requirements: Tuple[SignatureReadinessItem, ...] = ()
    required_approvals: Tuple[SignatureReadinessItem, ...] = ()
    required_signatures: Tuple[SignatureReadinessItem, ...] = ()
    responsible_parties: Tuple[SignatureReadinessItem, ...] = ()
    critical_dates: Tuple[SignatureReadinessItem, ...] = ()
    unresolved_risks: Tuple[SignatureReadinessItem, ...] = ()
    exceptions: Tuple[SignatureReadinessItem, ...] = ()
    dependencies: Tuple[SignatureReadinessItem, ...] = ()
    required_human_decisions: Tuple[SignatureReadinessItem, ...] = ()
    provenance_refs: Tuple[str, ...] = ()
    audit_refs: Tuple[str, ...] = ()
    status: SignatureReadinessStatus = SignatureReadinessStatus.NOT_READY
    assessed_at: Optional[datetime] = None
    history: Tuple[str, ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        transaction_readiness_id: str,
        opportunity_id: str,
        lifecycle_opportunity_id: str,
        decision_record_id: str,
        *,
        signature_package_id: Optional[str] = None,
        **kwargs,
    ) -> "SignatureReadinessPackage":
        for name, value in {
            "transaction_readiness_id": transaction_readiness_id,
            "opportunity_id": opportunity_id,
            "lifecycle_opportunity_id": lifecycle_opportunity_id,
            "decision_record_id": decision_record_id,
        }.items():
            if not value.strip():
                raise ValueError(f"{name} must be non-empty")
        return cls(
            signature_package_id=signature_package_id or f"SIG-{uuid4().hex[:16]}",
            transaction_readiness_id=transaction_readiness_id,
            opportunity_id=opportunity_id,
            lifecycle_opportunity_id=lifecycle_opportunity_id,
            decision_record_id=decision_record_id,
            **kwargs,
        )

    @property
    def has_investment_authority(self) -> bool:
        return False

    @property
    def has_human_authorization(self) -> bool:
        return False

    @property
    def has_signature_authority(self) -> bool:
        return False

    @property
    def has_execution_authority(self) -> bool:
        return False

    @property
    def approved(self) -> bool:
        return False

    @property
    def signed(self) -> bool:
        return False

    @property
    def executed(self) -> bool:
        return False

    def assess(self, *, at: Optional[datetime] = None) -> "SignatureReadinessPackage":
        """Assess completeness without changing any lifecycle or authority state."""
        items = self._all_items()
        required = [item for item in items if item.required]
        unsatisfied = [item for item in required if not item.satisfied]
        blocking_exceptions = [item for item in self.exceptions if item.required and not item.satisfied]

        if not items:
            status = SignatureReadinessStatus.NOT_READY
        elif blocking_exceptions:
            status = SignatureReadinessStatus.BLOCKED
        elif unsatisfied:
            status = SignatureReadinessStatus.INCOMPLETE
        elif any(not item.satisfied for item in self.exceptions):
            status = SignatureReadinessStatus.CONDITIONAL
        else:
            status = SignatureReadinessStatus.READY_FOR_HUMAN_SIGNATURE

        timestamp = at or datetime.now(timezone.utc)
        history_entry = f"{timestamp.isoformat()}:{status.value}"
        return SignatureReadinessPackage(
            signature_package_id=self.signature_package_id,
            transaction_readiness_id=self.transaction_readiness_id,
            opportunity_id=self.opportunity_id,
            lifecycle_opportunity_id=self.lifecycle_opportunity_id,
            decision_record_id=self.decision_record_id,
            transaction_terms_refs=self.transaction_terms_refs,
            capital_structure_refs=self.capital_structure_refs,
            diligence_status=self.diligence_status,
            financing_conditions=self.financing_conditions,
            contractual_requirements=self.contractual_requirements,
            required_approvals=self.required_approvals,
            required_signatures=self.required_signatures,
            responsible_parties=self.responsible_parties,
            critical_dates=self.critical_dates,
            unresolved_risks=self.unresolved_risks,
            exceptions=self.exceptions,
            dependencies=self.dependencies,
            required_human_decisions=self.required_human_decisions,
            provenance_refs=self.provenance_refs,
            audit_refs=self.audit_refs,
            status=status,
            assessed_at=timestamp,
            history=self.history + (history_entry,),
        )

    def _all_items(self) -> Tuple[SignatureReadinessItem, ...]:
        return (
            self.diligence_status
            + self.financing_conditions
            + self.contractual_requirements
            + self.required_approvals
            + self.required_signatures
            + self.responsible_parties
            + self.critical_dates
            + self.unresolved_risks
            + self.exceptions
            + self.dependencies
            + self.required_human_decisions
        )
