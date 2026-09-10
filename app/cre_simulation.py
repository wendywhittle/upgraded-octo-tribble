"""Explicit CRE-to-simulator boundary.

This adapter validates and labels structured underwriting inputs. It does not
calculate or approve an investment outcome. The independent simulator remains
the sole source of stochastic results.
"""
from dataclasses import dataclass, field
from typing import Mapping, Sequence

CRE_SIMULATION_VARIABLES = (
    "purchase_price", "gross_rent", "effective_income", "noi", "occupancy", "vacancy",
    "rent_growth", "expenses", "expense_growth", "capital_expenditures", "cap_rate",
    "financing_assumptions", "loan_amount", "loan_to_value", "interest_rate", "debt_service",
    "amortization_years", "hold_period", "exit_assumptions", "exit_cap_rate", "selling_cost_rate",
    "leasing_assumptions",
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
        return tuple(f"{name}={value}" for name, value in self.assumptions.items() if value is not None)
