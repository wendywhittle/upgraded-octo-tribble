"""Bounded research observation layer.

Research is supplied as explicit observations. This module records an
observation without pretending that the system independently verified it.
No external contact or investment authorization occurs here.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path


@dataclass(frozen=True)
class ResearchObservation:
    prospect_id: str
    source: str
    observed_at: str
    facts: tuple[str, ...]


def append_observation(
    path: str,
    observation: ResearchObservation,
) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "prospect_id": observation.prospect_id,
        "source": observation.source,
        "observed_at": observation.observed_at,
        "facts": list(observation.facts),
    }
    with target.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, sort_keys=True) + "\n")
