"""FastAPI endpoint for evidence-fed decision-intelligence analysis."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from app.analysis_pipeline import run_analysis
from app.cre_context import CREOpportunityContext
from app.decision_gate import evaluate_decision_gate
from app.decision_gate_endpoint import _derive_criteria
from app.memory import append_record


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    evidence: list[Dict[str, Any]] = Field(default_factory=list, max_length=200)
    initial_value: float = Field(default=100.0, gt=0)
    horizon_steps: int = Field(default=60, ge=1, le=10000)
    paths: int = Field(default=5000, ge=100, le=100000)
    seed: int = Field(default=42, ge=0)
    cre_context: Dict[str, Any] | None = None


def _serialize_gate(result: Any) -> Dict[str, Any]:
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


def evaluate_integrated_decision_gate(analysis: Dict[str, Any]) -> Dict[str, Any]:
    """Evaluate the gate from the completed server-side analysis result.

    The client cannot supply readiness state. The result of the real analysis
    pipeline is encoded and evaluated here, so missing/incomplete state fails closed.
    """
    encoded = jsonable_encoder(analysis)
    criteria = _derive_criteria(encoded)
    recommendation = (encoded.get("cre") or {}).get("decision", {}).get("state")
    gate = evaluate_decision_gate(criteria, system_recommendation=recommendation)
    serialized = _serialize_gate(gate)
    append_record({
        "record_type": "decision_gate_transition",
        "recorded_at": gate.audit_event.timestamp,
        "gate_state": gate.state.value,
        "readiness_criteria": serialized["readiness_criteria"],
        "blocking_conditions": serialized["blocking_conditions"],
        "system_recommendation": recommendation,
        "human_exception_status": None,
        "human_decision": None,
        "human_rationale": None,
        "decision_authority": None,
        "reason_for_reopening": gate.audit_event.reason,
    })
    return serialized


def build_analysis_router() -> APIRouter:
    router = APIRouter(prefix="/analysis", tags=["decision-intelligence"])

    @router.post("/run")
    def analyze(request: AnalysisRequest) -> Dict[str, Any]:
        try:
            cre_context = CREOpportunityContext(**request.cre_context) if request.cre_context else None
            result = run_analysis(
                question=request.question,
                evidence=request.evidence,
                initial_value=request.initial_value,
                horizon_steps=request.horizon_steps,
                paths=request.paths,
                seed=request.seed,
                cre_context=cre_context,
            )
            result["decision_gate"] = evaluate_integrated_decision_gate(result)
            return result
        except (TypeError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
