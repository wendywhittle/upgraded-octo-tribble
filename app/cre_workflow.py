"""Typed CRE workflow boundaries without prematurely implementing every stage."""
from enum import Enum


class CREWorkflowStage(str, Enum):
    OPPORTUNITY = "OPPORTUNITY"
    SCREENING = "SCREENING"
    UNDERWRITING = "UNDERWRITING"
    DUE_DILIGENCE = "DUE DILIGENCE"
    SCENARIO_ANALYSIS = "SCENARIO ANALYSIS"
    CAPITAL_STRUCTURE = "CAPITAL STRUCTURE"
    VALUE_CREATION = "VALUE CREATION"
    INVESTMENT_COMMITTEE = "INVESTMENT COMMITTEE"
    CAPITAL_ASSET = "CAPITAL / ASSET"
    OBSERVE_OUTCOME = "OBSERVE OUTCOME"
    EPISTEMIC_MEMORY = "EPISTEMIC MEMORY"


WORKFLOW_ORDER = tuple(CREWorkflowStage)


def next_stage(stage: CREWorkflowStage) -> CREWorkflowStage | None:
    """Return the next workflow boundary; None marks the terminal memory stage."""
    index = WORKFLOW_ORDER.index(stage)
    return WORKFLOW_ORDER[index + 1] if index + 1 < len(WORKFLOW_ORDER) else None
