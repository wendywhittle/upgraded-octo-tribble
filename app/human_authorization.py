"""Provider-neutral human authorization boundary.

This module records explicit human authorization decisions for prepared
investment and transaction packages. It does not authenticate users, sign
documents, execute transactions, move capital, close, fund, or mutate
portfolios.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Tuple
from uuid import uuid4


class HumanAuthorizationStatus(str, Enum):
    NOT_SUBMITTED = "NOT_SUBMITTED"
    AWAITING_HUMAN_REVIEW = "AWAITING_HUMAN_REVIEW"
    HUMAN_REVIEWED = "HUMAN_REVIEWED"
    AUTHORIZED = "AUTHORIZED"
    REJECTED = "REJECTED"
    CONDITIONAL_AUTHORIZATION = "CONDITIONAL_AUTHORIZATION"
    WITHDRAWN = "WITHDRAWN"


@dataclass(frozen=True)
class AuthorizationEvent:
    """Immutable record of an explicit human-supplied authorization event."""

    status: HumanAuthorizationStatus
    decision_maker_ref: str
    authority_role_ref: str
    reviewed_package_ref: str
    rationale: str
    at: datetime
    conditions: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        for name, value in {
            "decision_maker_ref": self.decision_maker_ref,
            "authority_role_ref": self.authority_role_ref,
            "reviewed_package_ref": self.reviewed_package_ref,
            "rationale": self.rationale,
        }.items():
            if not value.strip():
                raise ValueError(f"{name} must be non-empty")
        if self.status not in {
            HumanAuthorizationStatus.HUMAN_REVIEWED,
            HumanAuthorizationStatus.AUTHORIZED,
            HumanAuthorizationStatus.CONDITIONAL_AUTHORIZATION,
            HumanAuthorizationStatus.REJECTED,
            HumanAuthorizationStatus.WITHDRAWN,
        }:
            raise ValueError("AuthorizationEvent requires a valid human event state")
        if self.status is HumanAuthorizationStatus.CONDITIONAL_AUTHORIZATION and not self.conditions:
            raise ValueError("conditional authorization requires named conditions")


@dataclass(frozen=True)
class HumanAuthorizationRecord:
    """Immutable authorization record; readiness never creates authorization."""

    authorization_id: str
    opportunity_id: str
    lifecycle_opportunity_id: str
    decision_record_id: str
    transaction_readiness_id: str
    signature_readiness_id: str
    authorization_subject: str
    status: HumanAuthorizationStatus = HumanAuthorizationStatus.NOT_SUBMITTED
    reviewed_evidence_refs: Tuple[str, ...] = ()
    reviewed_risk_refs: Tuple[str, ...] = ()
    reviewed_exception_refs: Tuple[str, ...] = ()
    reviewed_condition_refs: Tuple[str, ...] = ()
    required_conditions_precedent: Tuple[str, ...] = ()
    critical_deadlines: Tuple[str, ...] = ()
    audit_refs: Tuple[str, ...] = ()
    events: Tuple[AuthorizationEvent, ...] = field(default_factory=tuple)

    @classmethod
    def create(
        cls,
        opportunity_id: str,
        lifecycle_opportunity_id: str,
        decision_record_id: str,
        transaction_readiness_id: str,
        signature_readiness_id: str,
        authorization_subject: str,
        *,
        authorization_id: Optional[str] = None,
        **kwargs,
    ) -> "HumanAuthorizationRecord":
        for name, value in {
            "opportunity_id": opportunity_id,
            "lifecycle_opportunity_id": lifecycle_opportunity_id,
            "decision_record_id": decision_record_id,
            "transaction_readiness_id": transaction_readiness_id,
            "signature_readiness_id": signature_readiness_id,
            "authorization_subject": authorization_subject,
        }.items():
            if not value.strip():
                raise ValueError(f"{name} must be non-empty")
        return cls(
            authorization_id=authorization_id or f"AUTH-{uuid4().hex[:16]}",
            opportunity_id=opportunity_id,
            lifecycle_opportunity_id=lifecycle_opportunity_id,
            decision_record_id=decision_record_id,
            transaction_readiness_id=transaction_readiness_id,
            signature_readiness_id=signature_readiness_id,
            authorization_subject=authorization_subject,
            **kwargs,
        )

    def submit_for_review(self, *, at: Optional[datetime] = None) -> "HumanAuthorizationRecord":
        """Prepare a review state; this does not authorize anything."""
        if self.status not in {
            HumanAuthorizationStatus.NOT_SUBMITTED,
            HumanAuthorizationStatus.WITHDRAWN,
        }:
            raise ValueError(f"Cannot submit from {self.status.value}")
        return self._with_status(HumanAuthorizationStatus.AWAITING_HUMAN_REVIEW, at=at)

    def mark_human_reviewed(
        self,
        *,
        decision_maker_ref: str,
        authority_role_ref: str,
        reviewed_package_ref: str,
        rationale: str,
        at: Optional[datetime] = None,
    ) -> "HumanAuthorizationRecord":
        """Record that a human reviewed the package, without authorizing it."""
        if self.status is not HumanAuthorizationStatus.AWAITING_HUMAN_REVIEW:
            raise ValueError("Human review requires AWAITING_HUMAN_REVIEW")
        event = AuthorizationEvent(
            HumanAuthorizationStatus.HUMAN_REVIEWED,
            decision_maker_ref,
            authority_role_ref,
            reviewed_package_ref,
            rationale,
            at or datetime.now(timezone.utc),
        )
        return self._append_event(event)

    def record_human_decision(
        self,
        *,
        status: HumanAuthorizationStatus,
        decision_maker_ref: str,
        authority_role_ref: str,
        reviewed_package_ref: str,
        rationale: str,
        conditions: Tuple[str, ...] = (),
        at: Optional[datetime] = None,
    ) -> "HumanAuthorizationRecord":
        """Record an explicit human decision supplied by the caller.

        No decision is inferred from readiness, recommendations, or lifecycle state.
        """
        if status not in {
            HumanAuthorizationStatus.AUTHORIZED,
            HumanAuthorizationStatus.CONDITIONAL_AUTHORIZATION,
            HumanAuthorizationStatus.REJECTED,
        }:
            raise ValueError("record_human_decision requires an explicit decision state")
        if self.status is not HumanAuthorizationStatus.HUMAN_REVIEWED:
            raise ValueError("Explicit human decision requires HUMAN_REVIEWED")
        event = AuthorizationEvent(
            status,
            decision_maker_ref,
            authority_role_ref,
            reviewed_package_ref,
            rationale,
            at or datetime.now(timezone.utc),
            conditions,
        )
        return self._append_event(event)

    def withdraw(self, *, at: Optional[datetime] = None, rationale: str) -> "HumanAuthorizationRecord":
        """Record explicit withdrawal while retaining prior authorization history."""
        if self.status not in {
            HumanAuthorizationStatus.AUTHORIZED,
            HumanAuthorizationStatus.CONDITIONAL_AUTHORIZATION,
            HumanAuthorizationStatus.HUMAN_REVIEWED,
        }:
            raise ValueError(f"Cannot withdraw from {self.status.value}")
        prior = self.events[-1]
        event = AuthorizationEvent(
            HumanAuthorizationStatus.WITHDRAWN,
            prior.decision_maker_ref,
            prior.authority_role_ref,
            prior.reviewed_package_ref,
            rationale,
            at or datetime.now(timezone.utc),
            prior.conditions,
        )
        return self._append_event(event)

    @property
    def has_investment_authority(self) -> bool:
        return False

    @property
    def has_execution_authority(self) -> bool:
        return False

    @property
    def has_signature_authority(self) -> bool:
        return False

    @property
    def signed(self) -> bool:
        return False

    @property
    def executed(self) -> bool:
        return False

    @property
    def closed(self) -> bool:
        return False

    @property
    def funded(self) -> bool:
        return False

    @property
    def portfolio_mutation_permitted(self) -> bool:
        return False

    @property
    def capital_transfer_permitted(self) -> bool:
        return False

    def _with_status(
        self,
        status: HumanAuthorizationStatus,
        *,
        at: Optional[datetime],
    ) -> "HumanAuthorizationRecord":
        timestamp = at or datetime.now(timezone.utc)
        return HumanAuthorizationRecord(
            authorization_id=self.authorization_id,
            opportunity_id=self.opportunity_id,
            lifecycle_opportunity_id=self.lifecycle_opportunity_id,
            decision_record_id=self.decision_record_id,
            transaction_readiness_id=self.transaction_readiness_id,
            signature_readiness_id=self.signature_readiness_id,
            authorization_subject=self.authorization_subject,
            status=status,
            reviewed_evidence_refs=self.reviewed_evidence_refs,
            reviewed_risk_refs=self.reviewed_risk_refs,
            reviewed_exception_refs=self.reviewed_exception_refs,
            reviewed_condition_refs=self.reviewed_condition_refs,
            required_conditions_precedent=self.required_conditions_precedent,
            critical_deadlines=self.critical_deadlines,
            audit_refs=self.audit_refs,
            events=self.events,
        )

    def _append_event(self, event: AuthorizationEvent) -> "HumanAuthorizationRecord":
        return HumanAuthorizationRecord(
            authorization_id=self.authorization_id,
            opportunity_id=self.opportunity_id,
            lifecycle_opportunity_id=self.lifecycle_opportunity_id,
            decision_record_id=self.decision_record_id,
            transaction_readiness_id=self.transaction_readiness_id,
            signature_readiness_id=self.signature_readiness_id,
            authorization_subject=self.authorization_subject,
            status=event.status,
            reviewed_evidence_refs=self.reviewed_evidence_refs,
            reviewed_risk_refs=self.reviewed_risk_refs,
            reviewed_exception_refs=self.reviewed_exception_refs,
            required_conditions_precedent=self.required_conditions_precedent,
            reviewed_condition_refs=self.reviewed_condition_refs,
            reviewed_exception_refs=self.reviewed_exception_refs,
            critical_deadlines=self.critical_deadlines,
            audit_refs=self.audit_refs,
            events=self.events + (event,),
        )
