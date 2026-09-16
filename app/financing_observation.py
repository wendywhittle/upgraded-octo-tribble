"""Provider-independent financing observation contract.

A financing observation records what an external capital source says or what
research discovers about financing. It is not evidence merely because it is
represented here. Validation and provenance remain explicit prerequisites for
using it as validated evidence.
"""

from dataclasses import asdict, dataclass, field
from typing import Dict, Optional, Tuple


VALIDATION_STATUSES = {
    "UNVALIDATED",
    "PARTIALLY_VALIDATED",
    "VALIDATED",
    "REJECTED",
}


@dataclass(frozen=True)
class FinancingObservation:
    """Immutable, provider-independent financing observation."""

    observation_id: str
    provider_id: str
    observed_at: str
    source_uri: Optional[str] = None
    source_label: Optional[str] = None
    financing_type: Optional[str] = None
    asset_classes: Tuple[str, ...] = field(default_factory=tuple)
    geography: Tuple[str, ...] = field(default_factory=tuple)
    loan_to_value: Optional[float] = None
    loan_to_cost: Optional[float] = None
    interest_rate: Optional[str] = None
    term: Optional[str] = None
    amortization: Optional[str] = None
    covenants: Tuple[str, ...] = field(default_factory=tuple)
    assumptions: Tuple[str, ...] = field(default_factory=tuple)
    limitations: Tuple[str, ...] = field(default_factory=tuple)
    validation_status: str = "UNVALIDATED"
    evidence_id: Optional[str] = None
    notes: Optional[str] = None

    def __post_init__(self) -> None:
        for name in ("asset_classes", "geography", "covenants", "assumptions", "limitations"):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        if not self.observation_id.strip():
            raise ValueError("observation_id must not be empty")
        if not self.provider_id.strip():
            raise ValueError("provider_id must not be empty")
        if not self.observed_at.strip():
            raise ValueError("observed_at must not be empty")
        if self.validation_status not in VALIDATION_STATUSES:
            raise ValueError(
                f"validation_status must be one of {sorted(VALIDATION_STATUSES)}"
            )
        if self.validation_status == "VALIDATED" and not self.evidence_id:
            raise ValueError("VALIDATED financing observations require evidence_id")
        if self.loan_to_value is not None and not 0 <= self.loan_to_value <= 100:
            raise ValueError("loan_to_value must be between 0 and 100")
        if self.loan_to_cost is not None and not 0 <= self.loan_to_cost <= 100:
            raise ValueError("loan_to_cost must be between 0 and 100")

    @property
    def is_validated_evidence(self) -> bool:
        return self.validation_status == "VALIDATED" and bool(self.evidence_id)

    def normalized(self) -> Dict[str, object]:
        """Return a stable representation suitable for API/UI boundaries."""
        return asdict(self)
