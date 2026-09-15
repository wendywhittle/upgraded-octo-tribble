"""Provider-neutral Decision Readiness contract for research-only analysis."""

from typing import Any, Dict, Iterable, List


DecisionReadinessStatus = str


def _condition(key: str, label: str, satisfied: bool, *, blocking: bool = True, detail: str = "") -> Dict[str, Any]:
    return {"key": key, "label": label, "satisfied": bool(satisfied), "blocking": blocking, "detail": detail}


def _as_list(value: Any) -> List[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _perspective_provenance(case: Any, perspectives: Iterable[Any]) -> List[Dict[str, Any]]:
    existing = getattr(case, "perspective_provenance", None) or []
    if existing:
        return list(existing)
    output = []
    for perspective in perspectives:
        if not isinstance(perspective, dict):
            continue
        output.append({
            "agent_id": perspective.get("agent_id"),
            "evidence_basis": perspective.get("evidence_basis", []),
            "reasoning_method": perspective.get("strategy", "unknown"),
            "model_version": perspective.get("model_version"),
            "independence": "shared_pipeline_inputs",
            "independence_limitation": "Structural perspective separation does not by itself prove model independence.",
        })
    return output


def build_decision_readiness(
    investment_case: Any,
    *,
    evidence: Dict[str, Any],
    simulation: Dict[str, Any],
    skeptic: Dict[str, Any],
    synthesis: Dict[str, Any],
    governance: Dict[str, Any],
) -> Dict[str, Any]:
    """Assess whether an assembled Investment Case is ready for human review.

    This function evaluates readiness only. It never grants authorization.
    """
    blocking_reasons: List[str] = []
    hard_stops: List[str] = []
    conditions: List[Dict[str, Any]] = []
    case_dict = investment_case.to_dict() if hasattr(investment_case, "to_dict") else dict(investment_case or {})

    usable_count = int(evidence.get("usable_count", 0) or 0)
    validation_reports = _as_list(evidence.get("validation", []))
    validation_failed = any(isinstance(report, dict) and report.get("decision_usable") is False for report in validation_reports)
    provenance_ok = all(
        isinstance(item, dict) and bool(item.get("evidence_id") or item.get("source")) and bool(item.get("provenance"))
        for item in _as_list(case_dict.get("evidence"))
    ) if case_dict.get("evidence") else False

    conditions.append(_condition("EVIDENCE_USABLE", "Usable decision evidence exists", usable_count > 0))
    conditions.append(_condition("EVIDENCE_VALIDATED", "Evidence validation has not failed", not validation_failed))
    conditions.append(_condition("EVIDENCE_PROVENANCE", "Evidence has identifiable provenance", provenance_ok, blocking=False, detail="Case evidence provenance is assessed when evidence is attached to the case."))

    sources = {item.get("source") for item in _as_list(case_dict.get("evidence")) if isinstance(item, dict) and item.get("source")}
    corroboration_assessed = usable_count <= 1 or len(sources) >= 2
    conditions.append(_condition("EVIDENCE_CORROBORATION", "Corroboration is satisfied or not materially required", corroboration_assessed, blocking=False, detail="Corroboration is not forced for a single-source case, but remains visible."))

    thesis = case_dict.get("thesis") or {}
    assumptions = case_dict.get("assumptions") or []
    calculations = case_dict.get("calculations")
    scenarios = case_dict.get("scenarios")
    downside = bool((simulation or {}).get("scenarios")) or bool((case_dict.get("risk") or {}).get("downside"))
    sensitivities = bool(case_dict.get("sensitivities") or (case_dict.get("risk") or {}).get("sensitivity"))
    unresolved = case_dict.get("case_derived_unresolved_questions") or []

    conditions.append(_condition("THESIS_PRESENT", "Investment thesis is explicit", bool(thesis)))
    conditions.append(_condition("ASSUMPTIONS_EXPLICIT", "Assumptions are explicit", bool(assumptions)))
    conditions.append(_condition("CALCULATIONS_VALID", "Calculations are represented without being mislabeled as evidence", calculations is not None, blocking=False))
    conditions.append(_condition("SCENARIO_COVERAGE", "Scenario analysis is represented", bool(scenarios), blocking=False))
    conditions.append(_condition("DOWNSIDE_ADDRESSED", "Downside is represented", downside))
    conditions.append(_condition("SENSITIVITY_ADDRESSED", "Sensitivity is represented where applicable", sensitivities, blocking=False))
    conditions.append(_condition("UNRESOLVED_QUESTIONS_IDENTIFIED", "Case-derived unresolved questions are identified", bool(unresolved), blocking=False))

    perspectives = case_dict.get("perspectives") or []
    perspective_provenance = _perspective_provenance(investment_case, perspectives)
    required_perspectives_present = len(perspectives) > 0
    tied_to_evidence = any(isinstance(item, dict) and (item.get("evidence_basis") or item.get("evidence")) for item in perspectives)
    conditions.append(_condition("PERSPECTIVES_PRESENT", "Required perspective outputs are present", required_perspectives_present))
    conditions.append(_condition("PERSPECTIVE_EVIDENCE_BASIS", "Perspectives expose an evidence basis", tied_to_evidence))
    conditions.append(_condition("PERSPECTIVE_PROVENANCE", "Perspective reasoning provenance is explicit", bool(perspective_provenance), blocking=False))

    simulation_valid = simulation.get("valid") is not False and bool(simulation)
    independent = simulation.get("independent_of_agents") is True
    conditions.append(_condition("RISK_SIMULATION_VALID", "Independent risk simulation is valid", simulation_valid))
    conditions.append(_condition("RISK_SIMULATION_INDEPENDENT", "Risk simulation declares independence from agent conclusions", independent))
    conditions.append(_condition("RISK_SCENARIO_COVERAGE", "Risk simulation contains scenario coverage", bool(simulation.get("scenarios")), blocking=False))
    conditions.append(_condition("TAIL_RISK_CONSIDERED", "Tail-risk consideration is represented", any(str(s.get("scenario", "")).lower() == "adversarial" for s in _as_list(simulation.get("scenarios"))), blocking=False))

    skeptic_valid = skeptic.get("valid", True) is not False
    objections = skeptic.get("challenges") or skeptic.get("objections") or []
    conditions.append(_condition("CONTRARIAN_VALID", "Contrarian / skeptic review is valid", skeptic_valid))
    conditions.append(_condition("CONTRARIAN_OBJECTIONS", "Contrarian objections or explicit no-objection state is represented", bool(objections) or skeptic.get("status") == "insufficient_data", blocking=False))

    governance_fields = {
        "autonomous_execution": governance.get("autonomous_execution", False),
        "brokerage_connectivity": governance.get("brokerage_connectivity", False),
        "portfolio_mutation": governance.get("portfolio_mutation", False),
        "investment_authority": governance.get("investment_authority", False),
    }
    for name, enabled in governance_fields.items():
        conditions.append(_condition(f"GOVERNANCE_{name.upper()}", f"{name} remains disabled", not enabled))

    conditions.append(_condition("HUMAN_AUTHORITY_REQUIRED", "Human authority remains required", governance.get("human_decision_required", True) is True))

    for condition in conditions:
        if condition["blocking"] and not condition["satisfied"]:
            blocking_reasons.append(condition["label"])
            hard_stops.append(condition["key"])

    if not synthesis.get("verdict"):
        blocking_reasons.append("No system synthesis available")
        hard_stops.append("NO_SYNTHESIS")

    if hard_stops:
        status = "NOT_READY"
        readiness_state = "CLOSED_BLOCKED"
    else:
        status = "READY_FOR_HUMAN_AUTHORITY"
        readiness_state = "OPEN_READY_FOR_HUMAN_AUTHORITY"

    return {
        "status": status,
        "readiness_state": readiness_state,
        "ready_for_human_authority": status == "READY_FOR_HUMAN_AUTHORITY",
        "case_id": getattr(investment_case, "case_id", case_dict.get("case_id")),
        "case_version": getattr(investment_case, "case_version", case_dict.get("case_version")),
        "mandatory_conditions": [c for c in conditions if c["blocking"]],
        "satisfied_conditions": [c for c in conditions if c["satisfied"]],
        "blocking_conditions": [c for c in conditions if c["blocking"] and not c["satisfied"]],
        "blocking_reasons": blocking_reasons,
        "hard_stops": hard_stops,
        "missing_evidence": [] if usable_count > 0 else ["usable decision evidence"],
        "unresolved_issues": list(unresolved),
        "perspective_provenance": perspective_provenance,
        "research_only": True,
        "human_decision_required": True,
        "human_authorization": None,
        "authorized": False,
        "executed": False,
    }
