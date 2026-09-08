from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI, HTTPException

from app.agent_registry import run_default_agents
from app.analysis_endpoint import build_analysis_router
from app.calibration_endpoint import build_calibration_router
from app.config import live_market_enabled, market_symbol_map, research_feed_urls
from app.evidence import apply_evidence_gate
from app.experiment_001_endpoint import build_experiment_001_router
from app.learning import build_learning_report
from app.learning_endpoint import LearningRequest, build_learning_router
from app.live_market_endpoint import build_live_market_router
from app.memory import append_record, build_record, read_records
from app.observer import observe
from app.prediction_resolution import resolve_prediction
from app.prediction_resolution_endpoint import PredictionResolutionRequest, build_prediction_resolution_router
from app.research_endpoint import build_research_router
from app.schemas import SimulationRequest
from app.simulator import run_monte_carlo
from app.skeptic import review as skeptic_review

app = FastAPI(title="AletheiaTelos", version="1.11.0", description="Research and decision intelligence system; not an autonomous trading system.")


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def detect_conflicts(agents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    conflicts: List[Dict[str, Any]] = []
    horizon_divergences: List[Dict[str, Any]] = []
    for i, left in enumerate(agents):
        for right in agents[i + 1:]:
            if left.get("direction") in {"LONG", "SHORT"} and right.get("direction") in {"LONG", "SHORT"} and left.get("direction") != right.get("direction"):
                if left.get("horizon") == right.get("horizon"):
                    conflicts.append({"type": "same_horizon_conflict", "agents": [left.get("agent_id"), right.get("agent_id")], "horizon": left.get("horizon"), "directions": [left.get("direction"), right.get("direction")]})
                else:
                    horizon_divergences.append({"type": "horizon_divergence", "agents": [left.get("agent_id"), right.get("agent_id")], "horizons": [left.get("horizon"), right.get("horizon")], "directions": [left.get("direction"), right.get("direction")]})
    return {"conflicts": conflicts, "horizon_divergences": horizon_divergences}


def synthesize(agents: List[Dict[str, Any]], conflict_data: Dict[str, List[Dict[str, Any]]], skeptic: Dict[str, Any]) -> Dict[str, Any]:
    if any(a.get("direction") == "NO_DATA" for a in agents):
        verdict = "NO_DATA"
    elif skeptic["recommendation"] == "hold":
        verdict = "HOLD"
    elif conflict_data["conflicts"]:
        verdict = "CONDITIONAL GO"
    else:
        verdict = "INVESTIGATE"
    long_score = sum(a.get("confidence", 0.0) for a in agents if a.get("direction") == "LONG")
    short_score = sum(a.get("confidence", 0.0) for a in agents if a.get("direction") == "SHORT")
    total = long_score + short_score
    return {"verdict": verdict, "conviction": round(abs(long_score - short_score) / total, 3) if total else 0.0, "long_evidence": round(long_score, 3), "short_evidence": round(short_score, 3), "conflict_count": len(conflict_data["conflicts"]), "key_risks": ["Financing sensitivity", "Valuation assumptions", "Downside scenario uncertainty"], "unresolved_questions": ["What evidence would invalidate the core thesis?", "Which assumptions are most sensitive?", "Does the downside case preserve an adequate margin of safety?"]}


app.include_router(build_analysis_router())
app.include_router(build_calibration_router())
app.include_router(build_prediction_resolution_router())
app.include_router(build_learning_router())
app.include_router(build_experiment_001_router())

# Explicit application-boundary fallbacks keep the public routes observable even if
# router composition is altered by a future integration refactor.
if not any(getattr(route, "path", None) == "/observer/learning" for route in app.routes):
    @app.post("/observer/learning")
    def observer_learning(request: LearningRequest) -> Dict[str, Any]:
        return build_learning_report(read_records(), bins=request.bins)

if not any(getattr(route, "path", None) == "/predictions/resolve" for route in app.routes):
    @app.post("/predictions/resolve")
    def resolve_prediction_route(request: PredictionResolutionRequest) -> Dict[str, Any]:
        prediction_id = request.prediction.get("prediction_id")
        if any(
            record.get("record_type") == "prediction_resolution"
            and record.get("prediction_id") == prediction_id
            for record in read_records()
        ):
            raise HTTPException(status_code=409, detail="prediction_id has already been resolved")
        try:
            result = resolve_prediction(
                request.prediction,
                request.outcome,
                request.resolved_at,
                request.outcome_source,
            )
            append_record(result)
            return result
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/")
def root():
    return {"system": "AletheiaTelos", "status": "operational", "version": "1.11.0", "live_market_data": live_market_enabled()}


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": timestamp(), "live_market_data": live_market_enabled()}


@app.get("/memory")
def memory():
    records = read_records()
    return {"count": len(records), "records": records}


feed_urls = research_feed_urls()
if feed_urls:
    app.include_router(build_research_router(feed_urls))

if live_market_enabled():
    app.include_router(build_live_market_router(market_symbol_map()))


@app.post("/simulate")
def simulate(request: SimulationRequest):
    raw_agents = run_default_agents(request.question)
    agents, evidence_validation = apply_evidence_gate(raw_agents)
    conflict_data = detect_conflicts(agents)
    simulation = run_monte_carlo(request.initial_value, request.horizon_steps, request.paths, request.seed, assumptions=[a for agent in agents for a in agent.get("assumptions", [])])
    skeptic = skeptic_review(agents, simulation)
    synthesis = synthesize(agents, conflict_data, skeptic)
    governance = {"human_decision_required": True, "autonomous_execution": False, "brokerage_connectivity": False}
    observer = observe(request.question, agents, conflict_data, simulation, skeptic, synthesis)
    record = build_record(request.question, agents, conflict_data, simulation, skeptic, synthesis, governance, request.seed)
    append_record(record)
    return {"system": "AletheiaTelos", "version": "1.11.0", "question": request.question, "timestamp": timestamp(), "agents": agents, "evidence_validation": evidence_validation, "conflicts": conflict_data["conflicts"], "horizon_divergences": conflict_data["horizon_divergences"], "simulation": simulation, "skeptic": skeptic, "observer": observer, "breaker": {"status": "pending", "decision": "pending", "human_decision_required": True}, "meta_intelligence": {"status": "active", "observation": "Independent perspectives and simulation distributions remain separately inspectable."}, "synthesis": synthesis, "governance": governance, "audit": {"reproducible": True, "simulation_seed": request.seed, "point_in_time_evidence_required": True, "evidence_gate": "active", "memory_recorded": True, "agent_registry": "active", "agent_runner": "active"}}
