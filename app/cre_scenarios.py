"""Typed CRE scenario contracts for independent simulation."""
from dataclasses import dataclass, field
from enum import Enum
from typing import Sequence


class CREScenario(str, Enum):
    BASE = "BASE"
    BULL = "BULL"
    BEAR = "BEAR"
    ADVERSARIAL = "ADVERSARIAL"
    TAIL_RISK = "TAIL RISK"


@dataclass(frozen=True)
class CREScenarioSpec:
    scenario: CREScenario
    assumptions: Sequence[str] = field(default_factory=tuple)
    affected_variables: Sequence[str] = field(default_factory=tuple)
    expected_direction: str | None = None
    severity: str | None = None
    uncertainty: Sequence[str] = field(default_factory=tuple)
    invalidation_conditions: Sequence[str] = field(default_factory=tuple)
    simulation_reference: str | None = None
    evidence_ids: Sequence[str] = field(default_factory=tuple)


def default_scenario_specs() -> tuple[CREScenarioSpec, ...]:
    """Return scenario shells only; values must come from evidence or explicit assumptions."""
    return tuple(CREScenarioSpec(scenario=s) for s in CREScenario)
