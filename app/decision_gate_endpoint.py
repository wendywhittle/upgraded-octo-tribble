"""API boundary for the formal Decision Gate."""
from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.decision_gate import (
    GateState,
    HumanDisposition,
    evaluate_decision_gate,
    record_human_decision,
)
from app.memory import append_record


class DecisionGateRequest(BaseModel):
    analysis: Dict[str, Any]
    previous_state: GateState | None = None


class HumanDecisionRequest(BaseModel):
    gate_state: GateState
    disposition: HumanDisposition
    rationale: str = Field(min_length=1, max_length=4000)
    exception_acknowledged: bool = False


def _derive_criteria(analysis: Dict[str, Any]) -> Dict[str, bool]:
    """Derive readiness from server-returned analysis without using recommendation/confidence."""
    cre = analysis.get("cre") or {}
    context = cre.get("context") or {}
    evidence = analysis.get("evidence") or {}
    financial = cre.get("financial_model") or {}
    agents = analysis.get("agents") or []
    adversarial = cre.get("adversarial_review") or {}
    simulation = cre.get("simulation") or {}
    governance = analysis.get("governance") or {}
    synthesis = analysis.get("synthesis") or {}
    conflicts = cre.get("conflicts") or []
    validation = evidence.get("validation") or []

    scenario_names = {
        str(item.get("scenario", "")).upper().replace(" ", "_")
        for item in simulation.get("scenarios", [])
        if isinstance(item, dict)
    }
    has_downside = bool({"BEAR", "ADVERSARIAL", "TAIL_RISK"} & scenario_names)
    validation_clean = all(
        isinstance(item, dict) and item.get("decision_usable") is True
        for item in validation
    ) if validation else False

    financial_missing = financial.get("missing_inputs") or []
    uncertainty = context.get("uncertainty") or []
    assumptions = context.get("assumptions") or []

    return {
        "OPPORTUNITY_DEFINED": bool(
            str(analysis.get("question", "")).strip()
            and context.get("opportunity_id")
            and context.get("asset_type")
            and context.get("location")
        ),
        "EVIDENCE_INTEGRITY": bool(
            evidence.get("count", 0) > 0
            and evidence.get("usable_count", 0) > 0
            and validation_clean
        ),
        "UNDERWRITING_COMPLETE": financial.get("status") == "CALCULATED" and not financial_missing,
        "MULTI_PERSPECTIVE_CHALLENGE_COMPLETE": len(agents) >= 6 and bool(analysis.get("skeptic")),
        "CONTRARIAN_REVIEW_COMPLETE": adversarial.get("status") == "reviewed" and bool(adversarial.get("challenges")),
        "SCENARIO_ANALYSIS_COMPLETE": bool(simulation.get("scenarios")) and has_downside,
        "CONFLICTS_CHARACTERIZED": all(
            isinstance(item, dict) and item.get("classification") in {"EXPLAINED", "ACCEPTED FOR HUMAN REVIEW", "BLOCKING"}
            for item in conflicts
        ),
        "MATERIAL_UNKNOWNS_CLASSIFIED": not financial_missing and not uncertainty and bool(assumptions),
        "GOVERNANCE_CHECK_PASSED": (
            governance.get("human_decision_required") is True
            and governance.get("autonomous_execution") is False
            and governance.get("brokerage_connectivity") is False
            and governance.get("portfolio_mutation") is False
        ),
        "DECISION_RECORD_COMPLETE": bool(
            synthesis
            and analysis.get("kaleidoscope")
            and analysis.get("audit", {}).get("research_only") is True
            and analysis.get("audit", {}).get("human_decision_required") is True
        ),
    }


def _serialize(result):
    return {
        "state": result.state.value,
        "display_status": result.display_status,
        "ready_for_human_authority": result.ready_for_human_authority,
        "system_can_authorize": result.system_can_authorize,
        "readiness_criteria": {k: v.value for k, v in result.readiness_criteria.items()},
        "blocking_conditions": [x.value for x in result.blocking_conditions],
        "hard_stops": [x.value for x in result.hard_stops],
        "system_recommendation": result.system_recommendation,
        "audit_event": {
            "timestamp": result.audit_event.timestamp,
            "from_state": result.audit_event.from_state.value if result.audit_event.from_state else None,
            "to_state": result.audit_event.to_state.value,
            "reason": result.audit_event.reason,
        } if result.audit_event else None,
    }


def build_decision_gate_router() -> APIRouter:
    router = APIRouter(prefix="/decision-gate", tags=["governance"])

    @router.post("/evaluate")
    def evaluate(request: DecisionGateRequest) -> Dict[str, Any]:
        criteria = _derive_criteria(request.analysis)
        recommendation = (request.analysis.get("cre") or {}).get("decision", {}).get("state")
        result = evaluate_decision_gate(criteria, previous_state=request.previous_state, system_recommendation=recommendation)
        append_record({
            "record_type": "decision_gate_transition",
            "recorded_at": result.audit_event.timestamp,
            "gate_state": result.state.value,
            "readiness_criteria": {k: v.value for k, v in result.readiness_criteria.items()},
            "blocking_conditions": [x.value for x in result.blocking_conditions],
            "system_recommendation": recommendation,
            "human_exception_status": None,
            "human_decision": None,
            "human_rationale": None,
            "decision_authority": None,
            "reason_for_reopening": result.audit_event.reason,
        })
        return _serialize(result)

    @router.post("/record-decision")
    def record_decision(request: HumanDecisionRequest) -> Dict[str, Any]:
        try:
            decision = record_human_decision(
                request.disposition,
                request.rationale,
                gate_state=request.gate_state,
                exception_acknowledged=request.exception_acknowledged,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc
        record = {
            "record_type": "human_decision",
            "recorded_at": decision.recorded_at,
            "gate_state": decision.system_gate_state.value,
            "human_exception_status": "EXCEPTION ACKNOWLEDGED" if decision.exception_acknowledged else None,
            "human_decision": decision.disposition.value,
            "human_rationale": decision.rationale,
            "decision_authority": decision.authority,
        }
        append_record(record)
        return record

    return router
