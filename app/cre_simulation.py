"""Explicit CRE-to-simulator boundary.

This adapter validates what underwriting is asking the independent simulator to
consider. It does not calculate or approve an investment outcome.
"""
from dataclasses import dataclass, field
from typing import Mapping, Sequence

CRE_SIMULATION_VARIABLES = (
    "purchase_price", "noi", "occupancy", "rent_growth", "vacancy", "expenses",
    "exit_assumptions", "financing_assumptions", "interest_rate", "hold_period",
    "cap_rate", "leasing_assumptions", "capital_expenditures",
)


@dataclass(frozen=True)
class CRESimulationRequest:
    opportunity_id: str
    assumptions: Mapping[str, float | str | None] = field(default_factory=dict)
    scenario_names: Sequence[str] = ("BASE", "BULL", "BEAR", "ADVERSARIAL", "TAIL RISK")
    evidence_ids: Sequence[str] = field(default_factory=tuple)

    def missing_variables(self, required: Sequence[str] = ("purchase_price", "noi")) -> tuple[str, ...]:
        return tuple(name for name in required if self.assumptions.get(name) is None)

    def is_ready(self, required: Sequence[str] = ("purchase_price", "noi")) -> bool:
        return not self.missing_variables(required)

    def assumption_labels(self) -> tuple[str, ...]:
        """Pass explicit assumption names downstream without inventing values."""
        return tuple(
            f"{name}={value}" for name, value in self.assumptions.items() if value is not None
        )
