"""Provider-neutral Decision Readiness contract for research-only analysis."""

from typing import Any, Dict, Iterable, List


DecisionReadinessStatus = str
_REQUIRED_PERSPECTIVES = {"researcher", "quant", "investor", "scientist", "systems", "skeptic", "contrarian", "governance"}


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
    """Assess readiness only. Never grant authorization."""
    blocking_reasons: List[str] = []
    hard_stops: List[str] = []
    conditions: List[Dict[str, Any]] = []
    case_dict = investment_case.to_dict() if hasattr(investment_case, "to_dict") else dict(investment_case or {})
    usable_count = int(evidence.get("usable_count", 0) or 0)
    validation_reports = _as_list(evidence.get("validation", []))
    validation_failed = any(isinstance(report, dict) and report.get("decision_usable") is False for report in validation_reports)
    case_evidence = _as_list(case_dict.get("evidence"))
    provenance_ok = bool(case_evidence) and all(
        isinstance(item, dict)
        and bool(item.get("evidence_id"))
        and bool(item.get("source"))
        and bool(item.get("provenance"))
        for item in case_evidence
    )
    conditions.append(_condition("EVIDENCE_USABLE", "Usable decision evidence exists", usable_count > 0))
    conditions.append(_condition("EVIDENCE_VALIDATED", "Evidence validation has not failed", not validation_failed))
    conditions.append(_condition("EVIDENCE_PROVENANCE", "Decision evidence has identity, source, and provenance", provenance_ok))
    sources = {item.get("source") for item in case_evidence if isinstance(item, dict) and item.get("source")}
    conditions.append(_condition("EVIDENCE_CORROBORATION", "Corroboration is satisfied or not materially required", usable_count <= 1 or len(sources) >= 2, blocking=False))

    thesis = case_dict.get("thesis") or {}
    assumptions = case_dict.get("assumptions") or []
    calculations = case_dict.get("calculations")
    scenarios = _as_list(case_dict.get("scenarios"))
    scenario_names = {str(s.get("scenario", "")).lower() for s in scenarios if isinstance(s, dict)}
    downside = bool({"bear", "adversarial"}.intersection(scenario_names)) and "bear" in scenario_names and "adversarial" in scenario_names
    sensitivities = bool(case_dict.get("sensitivities") or (case_dict.get("risk") or {}).get("sensitivity"))
    unresolved = case_dict.get("case_derived_unresolved_questions") or []
    conditions.append(_condition("THESIS_PRESENT", "Investment thesis is explicit", bool(thesis)))
    conditions.append(_condition("ASSUMPTIONS_EXPLICIT", "Assumptions are explicit", bool(assumptions)))
    conditions.append(_condition("CALCULATIONS_PRESENT", "Calculations are explicitly represented", calculations is not None))
    conditions.append(_condition("SCENARIO_COVERAGE", "Scenario analysis is represented", bool(scenarios)))
    conditions.append(_condition("DOWNSIDE_ADDRESSED", "Bear and adversarial downside scenarios are represented", downside))
    conditions.append(_condition("SENSITIVITY_ADDRESSED", "Sensitivity is represented where applicable", sensitivities, blocking=False))
    conditions.append(_condition("UNRESOLVED_QUESTIONS_IDENTIFIED", "Case-derived unresolved questions are identified", bool(unresolved), blocking=False))

    perspectives = case_dict.get("perspectives") or []
    perspective_ids = {p.get("agent_id") for p in perspectives if isinstance(p, dict)}
    perspective_provenance = _perspective_provenance(investment_case, perspectives)
    conditions.append(_condition("REQUIRED_PERSPECTIVES", "Required reasoning perspectives are present", _REQUIRED_PERSPECTIVES.issubset(perspective_ids)))
    tied_to_evidence = all(
        isinstance(p, dict) and bool(p.get("evidence_basis") or p.get("evidence"))
        for p in perspectives
    ) if perspectives else False
    conditions.append(_condition("PERSPECTIVE_EVIDENCE_BASIS", "All required perspectives expose an evidence basis", tied_to_evidence))
    conditions.append(_condition("PERSPECTIVE_PROVENANCE", "Perspective reasoning provenance is explicit", bool(perspective_provenance), blocking=False))
    conditions.append(_condition("PERSPECTIVE_INDEPENDENCE_DISCLOSED", "Independence limitations are disclosed", all(isinstance(p, dict) and p.get("independence_limitation") for p in perspective_provenance), blocking=False))

    simulation_present = bool(simulation)
    simulation_valid = simulation_present and simulation.get("valid", True) is not False
    independent = simulation.get("independent_of_agents") is True
    conditions.append(_condition("RISK_SIMULATION_VALID", "Independent risk simulation is valid", simulation_valid))
    conditions.append(_condition("RISK_SIMULATION_INDEPENDENT", "Risk simulation declares independence from agent conclusions", independent))
    conditions.append(_condition("RISK_SCENARIO_COVERAGE", "Risk simulation contains scenario coverage", bool(simulation.get("scenarios"))))
    conditions.append(_condition("TAIL_RISK_CONSIDERED", "Adversarial tail-risk consideration is represented", "adversarial" in {str(s.get("scenario", "")).lower() for s in _as_list(simulation.get("scenarios")) if isinstance(s, dict)}))

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

    readiness_state = "CLOSED_BLOCKED" if hard_stops else "OPEN_READY_FOR_HUMAN_AUTHORITY"
    return {
        "status": readiness_state,
        "legacy_status": "NOT_READY" if hard_stops else "READY_FOR_HUMAN_AUTHORITY",
        "readiness_state": readiness_state,
        "ready_for_human_authority": not hard_stops,
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
