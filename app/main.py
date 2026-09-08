from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI

from app.config import live_market_enabled, market_symbol_map, research_feed_urls
from app.evidence import apply_evidence_gate
from app.live_market_endpoint import build_live_market_router
from app.memory import append_record, build_record, read_records
from app.observer import observe
from app.research_endpoint import build_research_router
from app.schemas import SimulationRequest
from app.simulator import run_monte_carlo
from app.skeptic import review as skeptic_review


app = FastAPI(title="AletheiaTelos", version="1.7.0", description="Research and decision intelligence system; not an autonomous trading system.")


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_agent(agent_id: str, strategy: str, direction: str, confidence: float, horizon: str, thesis: str, contradictory: str) -> Dict[str, Any]:
    return {"agent_id": agent_id, "strategy": strategy, "direction": direction, "confidence": confidence, "horizon": horizon,
            "evidence": [{"evidence_id": f"{agent_id}-E1", "source": "AletheiaTelos simulation", "claim": thesis,
                          "observed_at": timestamp(), "retrieved_at": timestamp(), "provenance": {"type": "synthetic_demo", "point_in_time": True}}],
            "contradictory_evidence": [{"evidence_id": f"{agent_id}-C1", "source": "AletheiaTelos challenge set", "claim": contradictory,
                                         "observed_at": timestamp(), "retrieved_at": timestamp(), "provenance": {"type": "synthetic_demo", "independent": False}}],
            "invalidation_conditions": ["Material evidence contradicts the core thesis."], "data_timestamp": timestamp(),
            "model_version": "simulation-1.1", "regime_assumption": "Base-case market conditions", "capacity_constraint": None,
            "assumptions": ["Demo assumptions require replacement by verified data before investment use."]}


def generate_agents(question: str) -> List[Dict[str, Any]]:
    return [
        make_agent("researcher", "Fundamental Research", "LONG", .72, "medium", "The opportunity appears fundamentally supportable pending diligence.", "Asset-level assumptions may be overstated."),
        make_agent("quant", "Quantitative Underwriting", "LONG", .68, "medium", "The modeled return profile appears attractive under the base case.", "Downside sensitivity may be nonlinear."),
        make_agent("investor", "Investment Thesis", "LONG", .76, "long", "Entry valuation may provide an acceptable margin of safety.", "Exit assumptions could be too optimistic."),
        make_agent("scientist", "Scenario Analysis", "NEUTRAL", .61, "medium", "The result depends materially on assumptions that require testing.", "Scenario distributions may be wider than expected."),
        make_agent("systems", "Systems Risk", "SHORT", .64, "medium", "Interacting macro, financing, and operational risks could compound.", "The system may remain resilient under favorable conditions."),
        make_agent("contrarian", "Adversarial Challenge", "SHORT", .71, "short", "The consensus case may be underestimating a failure mode.", "The identified risk may ultimately prove immaterial."),
        make_agent("philosopher", "Epistemic Analysis", "NEUTRAL", .58, "long", "The quality of the decision depends on recognizing what is not known.", "Uncertainty itself may be difficult to quantify."),
        make_agent("observer", "Outcome Observation", "NEUTRAL", .55, "long", "The current state should be treated as a baseline for future attribution.", "Future outcomes may not cleanly identify causal drivers."),
        make_agent("meta_intelligence", "Meta-Intelligence", "NEUTRAL", .67, "medium", "The disagreement between bullish and defensive perspectives is decision-relevant.", "Some disagreement may arise from different assumptions rather than true conflict."),
        make_agent("governance", "CHARTER", "NEUTRAL", .95, "all", "Human Investment Committee authority remains mandatory.", "No autonomous investment authority is permitted."),
    ]


def detect_conflicts(agents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    conflicts, horizon_divergences = [], []
    for i, first in enumerate(agents):
        for second in agents[i + 1:]:
            if first.get("direction") in {"NEUTRAL", "NO_DATA"} or second.get("direction") in {"NEUTRAL", "NO_DATA"} or first.get("direction") == second.get("direction"):
                continue
            if first.get("horizon") == second.get("horizon"):
                conflicts.append({"agent_a": first["agent_id"], "agent_b": second["agent_id"], "direction_a": first["direction"], "direction_b": second["direction"], "horizon": first["horizon"], "type": "same_horizon_conflict"})
            else:
                horizon_divergences.append({"agent_a": first["agent_id"], "agent_b": second["agent_id"], "direction_a": first["direction"], "direction_b": second["direction"], "horizon_a": first["horizon"], "horizon_b": second["horizon"], "type": "horizon_divergence"})
    return {"conflicts": conflicts, "horizon_divergences": horizon_divergences}


def synthesize(agents: List[Dict[str, Any]], conflict_data: Dict[str, List[Dict[str, Any]]], skeptic: Dict[str, Any]) -> Dict[str, Any]:
    if any(a.get("direction") == "NO_DATA" for a in agents): verdict = "NO_DATA"
    elif skeptic["recommendation"] == "hold": verdict = "HOLD"
    elif conflict_data["conflicts"]: verdict = "CONDITIONAL GO"
    else: verdict = "INVESTIGATE"
    long_score = sum(a["confidence"] for a in agents if a.get("direction") == "LONG")
    short_score = sum(a["confidence"] for a in agents if a.get("direction") == "SHORT")
    total = long_score + short_score
    return {"verdict": verdict, "conviction": round(abs(long_score - short_score) / total, 3) if total else 0.0,
            "long_evidence": round(long_score, 3), "short_evidence": round(short_score, 3),
            "conflict_count": len(conflict_data["conflicts"]), "key_risks": ["Financing sensitivity", "Valuation assumptions", "Downside scenario uncertainty"],
            "unresolved_questions": ["What evidence would invalidate the core thesis?", "Which assumptions are most sensitive?", "Does the downside case preserve an adequate margin of safety?"]}


@app.get("/")
def root(): return {"system": "AletheiaTelos", "status": "operational", "version": "1.7.0", "live_market_data": live_market_enabled()}

@app.get("/health")
def health(): return {"status": "healthy", "timestamp": timestamp(), "live_market_data": live_market_enabled()}

@app.get("/memory")
def memory(): return {"count": len(read_records()), "records": read_records()}


feed_urls = research_feed_urls()
if feed_urls:
    app.include_router(build_research_router(feed_urls))

if live_market_enabled():
    app.include_router(build_live_market_router(market_symbol_map()))


@app.post("/simulate")
def simulate(request: SimulationRequest):
    raw_agents = generate_agents(request.question)
    agents, evidence_validation = apply_evidence_gate(raw_agents)
    conflict_data = detect_conflicts(agents)
    simulation = run_monte_carlo(request.initial_value, request.horizon_steps, request.paths, request.seed, assumptions=[a for agent in agents for a in agent.get("assumptions", [])])
    skeptic = skeptic_review(agents, simulation)
    synthesis = synthesize(agents, conflict_data, skeptic)
    governance = {"human_decision_required": True, "autonomous_execution": False, "brokerage_connectivity": False}
    observer = observe(request.question, agents, conflict_data, simulation, skeptic, synthesis)
    record = build_record(request.question, agents, conflict_data, simulation, skeptic, synthesis, governance, request.seed)
    append_record(record)
    return {"system": "AletheiaTelos", "version": "1.7.0", "question": request.question, "timestamp": timestamp(), "agents": agents,
            "evidence_validation": evidence_validation, "conflicts": conflict_data["conflicts"], "horizon_divergences": conflict_data["horizon_divergences"], "simulation": simulation,
            "skeptic": skeptic, "observer": observer, "breaker": {"status": "pending", "decision": "pending", "human_decision_required": True},
            "meta_intelligence": {"status": "active", "observation": "Independent perspectives and simulation distributions remain separately inspectable."},
            "synthesis": synthesis, "governance": governance,
            "audit": {"reproducible": True, "simulation_seed": request.seed, "point_in_time_evidence_required": True, "evidence_gate": "active", "memory_recorded": True}}
