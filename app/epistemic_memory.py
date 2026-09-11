"""Typed, append-only epistemic memory contract.

This module defines the boundary between analytical artifacts and future
institutional memory. It intentionally contains no financial calculations,
authorization logic, or execution capability.
"""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field


EpistemicRecordType = Literal[
    "evidence",
    "knowledge",
    "claim",
    "assumption",
    "hypothesis",
    "calculation",
    "interpretation",
    "recommendation",
    "authorization",
    "outcome",
    "attribution",
    "lesson",
    "contradiction",
]

RecordStatus = Literal["active", "superseded", "unresolved", "resolved", "observed"]


class EpistemicRecord(BaseModel):
    """Common immutable envelope for an institutional memory record."""

    model_config = ConfigDict(frozen=True)

    record_id: str = Field(min_length=1)
    record_type: EpistemicRecordType
    created_at: datetime
    effective_at: Optional[datetime] = None
    observed_at: Optional[datetime] = None
    source_refs: List[str] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)
    related_record_ids: List[str] = Field(default_factory=list)
    status: RecordStatus = "active"
    content: Dict[str, Any] = Field(default_factory=dict)
    confidence: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    uncertainty: Optional[str] = None
    supersedes: Optional[str] = None
    contradiction_of: List[str] = Field(default_factory=list)

    @property
    def has_authority(self) -> bool:
        """Memory records never grant authority by their existence."""
        return False


class EpistemicRevision(BaseModel):
    """Explicit historical transition; never an in-place mutation."""

    model_config = ConfigDict(frozen=True)

    revision_id: str = Field(min_length=1)
    prior_record_id: str = Field(min_length=1)
    new_record_id: str = Field(min_length=1)
    reason: str = Field(min_length=1)
    evidence_refs: List[str] = Field(default_factory=list)
    created_at: datetime


class ContradictionRecord(BaseModel):
    """First-class disagreement record; resolution is intentionally external."""

    model_config = ConfigDict(frozen=True)

    record_id: str = Field(min_length=1)
    record_type: Literal["contradiction"] = "contradiction"
    subject_record_ids: List[str] = Field(min_length=2)
    description: str = Field(min_length=1)
    status: Literal["unresolved", "resolved"] = "unresolved"
    resolution_record_id: Optional[str] = None
    created_at: datetime


def new_record_id(record_type: EpistemicRecordType, suffix: str) -> str:
    """Create a deterministic-format identifier without introducing authority."""
    return f"{record_type}:{suffix}"


def utc_now() -> datetime:
    return datetime.now(timezone.utc)
