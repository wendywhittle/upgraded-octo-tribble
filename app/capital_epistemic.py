"""Minimal provider-neutral epistemic contract for the Capital Engine.

This module is intentionally small. It proves the boundary between source
observations and admitted institutional evidence without requiring a provider,
database, infrastructure, or execution capability.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional, Tuple


class EpistemicStatus(str, Enum):
    VALID = "VALID"
    NO_DATA = "NO_DATA"
    UNKNOWN = "UNKNOWN"
    UNVERIFIED = "UNVERIFIED"
    AMBIGUOUS = "AMBIGUOUS"
    CONFLICTED = "CONFLICTED"
    STALE = "STALE"
    REVISED = "REVISED"
    INSUFFICIENT_EVIDENCE = "INSUFFICIENT_EVIDENCE"
    REJECTED = "REJECTED"


@dataclass(frozen=True)
class UsageState:
    retrievable: bool = False
    storable: bool = False
    transformable: bool = False
    displayable: bool = False
    retainable: bool = False
    redistributable: bool = False

    @property
    def durable_evidence_allowed(self) -> bool:
        return self.storable and self.transformable and self.retainable


@dataclass(frozen=True)
class Subject:
    subject_id: str
    subject_type: str
    security_id: Optional[str] = None
    listing_id: Optional[str] = None
    provider_id: Optional[str] = None
    ticker: Optional[str] = None
    exchange: Optional[str] = None
    mic: Optional[str] = None
    identifiers: Dict[str, str] = field(default_factory=dict)


@dataclass(frozen=True)
class RawObservation:
    source_id: str
    subject: Subject
    value: Any
    observed_at: Optional[str]
    effective_period: Optional[str]
    published_at: Optional[str]
    available_at: Optional[str]
    retrieved_at: str
    revision_id: Optional[str] = None
    revised_from_revision_id: Optional[str] = None
    usage: UsageState = field(default_factory=UsageState)
    raw_fingerprint: str = ""


@dataclass(frozen=True)
class NormalizedObservation:
    raw: RawObservation
    value: Any
    unit: Optional[str]
    currency: Optional[str]
    transformation: str
    transformation_kind: str = "mechanical"

    def lineage(self) -> Dict[str, str]:
        return {
            "source_id": self.raw.source_id,
            "raw_fingerprint": self.raw.raw_fingerprint,
            "transformation": self.transformation,
            "transformation_kind": self.transformation_kind,
        }


@dataclass(frozen=True)
class ValidationResult:
    status: EpistemicStatus
    reasons: Tuple[str, ...] = ()


@dataclass(frozen=True)
class KnowledgeState:
    decision_time: str
    published_by_decision: bool
    available_by_decision: bool
    retrieved_by_decision: bool

    @property
    def knowable(self) -> bool:
        return (
            self.published_by_decision
            and self.available_by_decision
            and self.retrieved_by_decision
        )


@dataclass(frozen=True)
class EvidenceAdmission:
    status: EpistemicStatus
    reasons: Tuple[str, ...]
    knowledge_state: KnowledgeState

    @property
    def admitted(self) -> bool:
        return self.status == EpistemicStatus.VALID


@dataclass(frozen=True)
class Evidence:
    observation: NormalizedObservation
    validation: ValidationResult
    provenance: Dict[str, Any]
    admission: EvidenceAdmission

    @property
    def execution_authority(self) -> bool:
        return False


def _parse(value: Optional[str]) -> Optional[datetime]:
    if value is None:
        return None
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def knowledge_state(raw: RawObservation, decision_time: str) -> KnowledgeState:
    decision = _parse(decision_time)
    assert decision is not None
    published = _parse(raw.published_at)
    available = _parse(raw.available_at)
    retrieved = _parse(raw.retrieved_at)
    return KnowledgeState(
        decision_time=decision.isoformat(),
        published_by_decision=published is not None and published <= decision,
        available_by_decision=available is not None and available <= decision,
        retrieved_by_decision=retrieved is not None and retrieved <= decision,
    )


def validate_observation(observation: NormalizedObservation) -> ValidationResult:
    raw = observation.raw
    reasons = []
    if not raw.source_id:
        reasons.append("missing source identity")
    if not raw.subject.subject_id:
        reasons.append("missing subject identity")
    if raw.value is None:
        reasons.append("missing observation value")
    if observation.transformation_kind != "mechanical":
        reasons.append("semantic interpretation cannot be normalization")
    if not raw.observed_at and not raw.effective_period:
        reasons.append("missing temporal context")
    if not raw.usage.transformable:
        reasons.append("usage does not permit transformation")
    if reasons:
        return ValidationResult(EpistemicStatus.REJECTED, tuple(reasons))
    return ValidationResult(EpistemicStatus.VALID)


def _is_conflict(
    observation: NormalizedObservation,
    competing: NormalizedObservation,
) -> bool:
    left = observation.raw
    right = competing.raw
    return (
        left.subject.subject_id == right.subject.subject_id
        and left.effective_period == right.effective_period
        and left.value != right.value
    )


def admit_evidence(
    observation: NormalizedObservation,
    validation: ValidationResult,
    decision_time: str,
    *,
    conflicted: bool = False,
    conflicting_observations: Tuple[NormalizedObservation, ...] = (),
    stale: bool = False,
    provenance_available: bool = True,
) -> EvidenceAdmission:
    raw = observation.raw
    state = knowledge_state(raw, decision_time)
    reasons = list(validation.reasons)
    actual_conflict = conflicted or any(
        _is_conflict(observation, competing) for competing in conflicting_observations
    )

    if not raw.subject.subject_id:
        return EvidenceAdmission(EpistemicStatus.AMBIGUOUS, ("subject identity is required",), state)
    if actual_conflict:
        return EvidenceAdmission(EpistemicStatus.CONFLICTED, ("unresolved source conflict",), state)
    if stale:
        return EvidenceAdmission(EpistemicStatus.STALE, ("observation is outside permitted freshness",), state)
    if not provenance_available:
        return EvidenceAdmission(EpistemicStatus.INSUFFICIENT_EVIDENCE, ("provenance is unavailable",), state)
    if not state.knowable:
        return EvidenceAdmission(EpistemicStatus.INSUFFICIENT_EVIDENCE, ("observation was not knowable by decision time",), state)
    if not raw.usage.durable_evidence_allowed:
        return EvidenceAdmission(EpistemicStatus.REJECTED, ("usage is incompatible with durable evidence",), state)
    if validation.status != EpistemicStatus.VALID:
        return EvidenceAdmission(EpistemicStatus.REJECTED, tuple(reasons) or ("validation failed",), state)
    return EvidenceAdmission(EpistemicStatus.VALID, (), state)


def build_evidence(
    observation: NormalizedObservation,
    validation: ValidationResult,
    admission: EvidenceAdmission,
) -> Evidence:
    provenance = {
        "source_id": observation.raw.source_id,
        "subject_id": observation.raw.subject.subject_id,
        "raw_fingerprint": observation.raw.raw_fingerprint,
        "observed_at": observation.raw.observed_at,
        "effective_period": observation.raw.effective_period,
        "published_at": observation.raw.published_at,
        "available_at": observation.raw.available_at,
        "retrieved_at": observation.raw.retrieved_at,
        "revision_id": observation.raw.revision_id,
        "revised_from_revision_id": observation.raw.revised_from_revision_id,
        "transformation": observation.lineage(),
        "usage": observation.raw.usage,
    }
    return Evidence(observation, validation, provenance, admission)
