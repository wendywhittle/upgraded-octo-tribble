"""Run the bounded growth loop from explicit fixture observations."""

from __future__ import annotations

import json
from pathlib import Path

from .loop import LoopResult, run_once
from .research import ResearchObservation
from .state import GrowthStore


def load_observation(path: str) -> ResearchObservation:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return ResearchObservation(
        prospect_id=data["prospect_id"],
        source=data["source"],
        observed_at=data["observed_at"],
        facts=tuple(data["facts"]),
    )


def run_fixture(
    db_path: str,
    observation_log: str,
    observation_fixture: str,
) -> LoopResult:
    observation = load_observation(observation_fixture)
    store = GrowthStore(db_path)
    return run_once(store, observation.prospect_id, observation_log, observation)
