"""Provider-neutral Decision Readiness boundary for research-only analysis."""

from typing import Any, Dict


DecisionReadinessStatus = str


def build_decision_readiness(
    investment_case: Any,
    *,
    evidence: Dict[str, Any],
    simulation: Dict[str, Any],
    skeptic: Dict[str, Any],
    synthesis: Dict[str, Any],
    governance: Dict[str, Any],
) -> Dict[str, Any]:
    """Assess whether an assembled Investment Case is ready for the governance gate."""
    blocking_reasons = []
    hard_stops = []

    if evidence.get("usable_count", 0) <= 0:
        blocking_reasons.append("No usable evidence")
        hard_stops.append("NO_USABLE_EVIDENCE")

    validation = evidence.get("validation", [])
    validation_reports = validation if isinstance(validation, list) else [validation]
    if any(isinstance(report, dict) and report.get("decision_usable") is False for report in validation_reports):
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
        status = "NOT_READY"
    elif not synthesis.get("verdict"):
        status = "NOT_READY"
    else:
        status = "READY_FOR_HUMAN_AUTHORITY"

    return {
        "status": status,
        "ready_for_human_authority": status == "READY_FOR_HUMAN_AUTHORITY",
        "case_id": getattr(investment_case, "case_id", None),
        "case_version": getattr(investment_case, "case_version", None),
        "blocking_reasons": blocking_reasons,
        "hard_stops": hard_stops,
        "research_only": True,
        "human_authorization": None,
        "authorized": False,
        "executed": False,
    }
