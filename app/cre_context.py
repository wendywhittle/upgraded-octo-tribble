"""Shared, evidence-aware context for the CRE intelligence loop.

The context is deliberately a data contract. It does not make an investment
recommendation and it never fills missing underwriting values with defaults.
"""
from dataclasses import dataclass, field
from typing import Mapping, Sequence


CRE_CONTEXT_FIELDS = (
    "purchase_price", "noi", "occupancy", "rent_growth", "vacancy", "expenses",
    "cap_rate", "financing_assumptions", "interest_rate", "hold_period",
    "exit_assumptions", "leasing_assumptions", "capital_expenditures",
    "value_creation_assumptions",
)


@dataclass(frozen=True)
class CREOpportunityContext:
    opportunity_id: str
    property_id: str
    asset_type: str
    location: str
    purchase_price: float | None = None
    noi: float | None = None
    occupancy: float | None = None
    rent_growth: float | None = None
    vacancy: float | None = None
    expenses: float | None = None
    cap_rate: float | None = None
    financing_assumptions: Mapping[str, float | str | None] = field(default_factory=dict)
    interest_rate: float | None = None
    hold_period: float | None = None
    exit_assumptions: Mapping[str, float | str | None] = field(default_factory=dict)
    leasing_assumptions: Mapping[str, float | str | None] = field(default_factory=dict)
    capital_expenditures: float | None = None
    value_creation_assumptions: Sequence[str] = field(default_factory=tuple)
    evidence: Sequence[str] = field(default_factory=tuple)
    contradictory_evidence: Sequence[str] = field(default_factory=tuple)
    uncertainty: Sequence[str] = field(default_factory=tuple)
    assumptions: Sequence[str] = field(default_factory=tuple)
    missing_inputs: Sequence[str] = field(default_factory=tuple)
    evidence_metadata: Mapping[str, Mapping[str, object]] = field(default_factory=dict)

    def missing_required(self) -> tuple[str, ...]:
        required = ("opportunity_id", "property_id", "asset_type", "location", "purchase_price", "noi")
        missing = [name for name in required if not getattr(self, name)]
        return tuple(missing)

    def evidence_quality_flags(self) -> tuple[str, ...]:
        flags: list[str] = []
        for evidence_id, metadata in self.evidence_metadata.items():
            if metadata.get("stale") is True:
                flags.append(f"stale:{evidence_id}")
            if metadata.get("integrity") in {"unknown", "failed"}:
                flags.append(f"integrity:{evidence_id}")
        return tuple(flags)

    def assumption_labels(self) -> tuple[str, ...]:
        labels = list(self.assumptions)
        for field_name in CRE_CONTEXT_FIELDS:
            value = getattr(self, field_name)
            if value is not None and value != {}:
                labels.append(f"{field_name}={value}")
        return tuple(labels)
