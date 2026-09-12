"""First-class Decision Gate for research-only institutional readiness."""

from enum import Enum
from typing import Any, Dict


class DecisionGateState(str, Enum):
    CLOSED = "CLOSED"
    CLOSED_BLOCKED = "CLOSED_BLOCKED"
    OPEN_READY_FOR_HUMAN_AUTHORITY = "OPEN_READY_FOR_HUMAN_AUTHORITY"


def build_decision_gate(
    evidence: Dict[str, Any],
    conflicts: Dict[str, Any],
    simulation: Dict[str, Any],
    skeptic: Dict[str, Any],
    synthesis: Dict[str, Any],
    governance: Dict[str, Any],
    contrarian_status: str = "not_available",
) -> Dict[str, Any]:
    """Assess readiness only; never infer or grant human authority."""
    blocking_reasons = []
    hard_stops = []

    if evidence.get("usable_count", 0) <= 0:
        blocking_reasons.append("No usable evidence")
        hard_stops.append("NO_USABLE_EVIDENCE")
    if evidence.get("validation", {}).get("status") == "failed":
        blocking_reasons.append("Evidence validation failed")
        hard_stops.append("EVIDENCE_VALIDATION_FAILED")
    if simulation.get("valid") is False:
        blocking_reasons.append("Independent risk simulation invalid")
        hard_stops.append("INVALID_RISK_SIMULATION")
    if skeptic.get("valid") is False:
        blocking_reasons.append("Skeptic review invalid")
        hard_stops.append("INVALID_SKEPTIC_REVIEW")

    prohibited = {
        "autonomous_execution": governance.get("autonomous_execution", False),
        "brokerage_connectivity": governance.get("brokerage_connectivity", False),
        "portfolio_mutation": governance.get("portfolio_mutation", False),
        "investment_authority": governance.get("investment_authority", False),
    }
    for name, enabled in prohibited.items():
        if enabled:
            blocking_reasons.append(f"Prohibited condition enabled: {name}")
            hard_stops.append(f"PROHIBITED_{name.upper()}")

    if not synthesis.get("verdict"):
        blocking_reasons.append("No system synthesis available")

    if blocking_reasons and hard_stops:
        state = DecisionGateState.CLOSED_BLOCKED
    elif not synthesis.get("verdict"):
        state = DecisionGateState.CLOSED
    else:
        state = DecisionGateState.OPEN_READY_FOR_HUMAN_AUTHORITY

    return {
        "state": state.value,
        "ready_for_human_authority": state == DecisionGateState.OPEN_READY_FOR_HUMAN_AUTHORITY,
        "human_decision_required": True,
        "human_decision": None,
        "human_authorization": None,
        "approval": None,
        "evidence_status": evidence,
        "unresolved_conflicts": conflicts.get("conflicts", []) + conflicts.get("horizon_divergences", []),
        "independent_risk": simulation,
        "contrarian_review_status": contrarian_status,
        "hard_stops": hard_stops,
        "blocking_reasons": blocking_reasons,
        "system_synthesis_verdict": synthesis.get("verdict"),
        "research_only": True,
        "autonomous_execution": False,
        "brokerage_connectivity": False,
        "portfolio_mutation": False,
        "investment_authority": False,
    }
