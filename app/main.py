from datetime import datetime, timezone
from typing import Any, Dict, List

from fastapi import FastAPI
from pydantic import BaseModel


app = FastAPI(
    title="AletheiaTelos",
    version="1.2.0",
    description="Institutional Real Estate Investment Intelligence",
)


class SimulationRequest(BaseModel):
    question: str


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


def make_agent(
    agent_id: str,
    strategy: str,
    direction: str,
    confidence: float,
    horizon: str,
    thesis: str,
    contradictory: str,
) -> Dict[str, Any]:
    return {
        "agent_id": agent_id,
        "strategy": strategy,
        "direction": direction,
        "confidence": confidence,
        "horizon": horizon,
        "evidence": [
            {
                "evidence_id": f"{agent_id}-E1",
                "source": "AletheiaTelos simulation",
                "claim": thesis,
                "observed_at": timestamp(),
                "retrieved_at": timestamp(),
            }
        ],
        "contradictory_evidence": [
            {
                "evidence_id": f"{agent_id}-C1",
                "source": "AletheiaTelos challenge set",
                "claim": contradictory,
                "observed_at": timestamp(),
                "retrieved_at": timestamp(),
            }
        ],
        "invalidation_conditions": [
            "Material evidence contradicts the core thesis."
        ],
        "data_timestamp": timestamp(),
        "model_version": "simulation-1.0",
        "regime_assumption": "Base-case market conditions",
        "capacity_constraint": None,
    }


def generate_agents(question: str) -> List[Dict[str, Any]]:
    return [
        make_agent(
            "researcher",
            "Fundamental Research",
            "LONG",
            0.72,
            "medium",
            "The opportunity appears fundamentally supportable pending diligence.",
            "Asset-level assumptions may be overstated.",
        ),
        make_agent(
            "quant",
            "Quantitative Underwriting",
            "LONG",
            0.68,
            "medium",
            "The modeled return profile appears attractive under the base case.",
            "Downside sensitivity may be nonlinear.",
        ),
        make_agent(
            "investor",
            "Investment Thesis",
            "LONG",
            0.76,
            "long",
            "Entry valuation may provide an acceptable margin of safety.",
            "Exit assumptions could be too optimistic.",
        ),
        make_agent(
            "scientist",
            "Scenario Analysis",
            "NEUTRAL",
            0.61,
            "medium",
            "The result depends materially on assumptions that require testing.",
            "Scenario distributions may be wider than expected.",
        ),
        make_agent(
            "systems",
            "Systems Risk",
            "SHORT",
            0.64,
            "medium",
            "Interacting macro, financing, and operational risks could compound.",
            "The system may remain resilient under favorable conditions.",
        ),
        make_agent(
            "contrarian",
            "Adversarial Challenge",
            "SHORT",
            0.71,
            "short",
            "The consensus case may be underestimating a failure mode.",
            "The identified risk may ultimately prove immaterial.",
        ),
        make_agent(
            "philosopher",
            "Epistemic Analysis",
            "NEUTRAL",
            0.58,
            "long",
            "The quality of the decision depends on recognizing what is not known.",
            "Uncertainty itself may be difficult to quantify.",
        ),
        make_agent(
            "observer",
            "Outcome Observation",
            "NEUTRAL",
            0.55,
            "long",
            "The current state should be treated as a baseline for future attribution.",
            "Future outcomes may not cleanly identify causal drivers.",
        ),
        make_agent(
            "meta_intelligence",
            "Meta-Intelligence",
            "NEUTRAL",
            0.67,
            "medium",
            "The disagreement between bullish and defensive perspectives is decision-relevant.",
            "Some apparent disagreement may arise from different assumptions rather than true conflict.",
        ),
        make_agent(
            "governance",
            "CHARTER",
            "NEUTRAL",
            0.95,
            "all",
            "Human Investment Committee authority remains mandatory.",
            "No autonomous investment authority is permitted.",
        ),
    ]


def detect_conflicts(agents: List[Dict[str, Any]]) -> Dict[str, List[Dict[str, Any]]]:
    conflicts = []
    horizon_divergences = []

    for i, first in enumerate(agents):
        for second in agents[i + 1 :]:
            if first["direction"] == "NEUTRAL" or second["direction"] == "NEUTRAL":
                continue

            if first["direction"] == second["direction"]:
                continue

            if first["horizon"] == second["horizon"]:
                conflicts.append(
                    {
                        "agent_a": first["agent_id"],
                        "agent_b": second["agent_id"],
                        "direction_a": first["direction"],
                        "direction_b": second["direction"],
                        "horizon": first["horizon"],
                        "type": "same_horizon_conflict",
                    }
                )
            else:
                horizon_divergences.append(
                    {
                        "agent_a": first["agent_id"],
                        "agent_b": second["agent_id"],
                        "direction_a": first["direction"],
                        "direction_b": second["direction"],
                        "horizon_a": first["horizon"],
                        "horizon_b": second["horizon"],
                        "type": "horizon_divergence",
                    }
                )

    return {
        "conflicts": conflicts,
        "horizon_divergences": horizon_divergences,
    }


def synthesize(
    agents: List[Dict[str, Any]],
    conflict_data: Dict[str, List[Dict[str, Any]]],
) -> Dict[str, Any]:
    bullish = [
        a for a in agents
        if a["direction"] == "LONG"
    ]

    bearish = [
        a for a in agents
        if a["direction"] == "SHORT"
    ]

    long_score = sum(a["confidence"] for a in bullish)
    short_score = sum(a["confidence"] for a in bearish)

    total = long_score + short_score

    conviction = (
        abs(long_score - short_score) / total
        if total
        else 0.0
    )

    if conflict_data["conflicts"]:
        verdict = "CONDITIONAL GO"
    elif long_score > short_score:
        verdict = "INVESTIGATE"
    else:
        verdict = "HOLD"

    return {
        "verdict": verdict,
        "conviction": round(conviction, 3),
        "long_evidence": round(long_score, 3),
        "short_evidence": round(short_score, 3),
        "conflict_count": len(conflict_data["conflicts"]),
        "key_risks": [
            "Financing sensitivity",
            "Valuation assumptions",
            "Downside scenario uncertainty",
        ],
        "unresolved_questions": [
            "What evidence would invalidate the core thesis?",
            "Which assumptions are most sensitive?",
            "Does the downside case preserve an adequate margin of safety?",
        ],
    }


@app.get("/")
def root():
    return {
        "system": "AletheiaTelos",
        "status": "operational",
        "version": "1.2.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "timestamp": timestamp(),
    }


@app.post("/simulate")
def simulate(request: SimulationRequest):
    agents = generate_agents(request.question)

    conflict_data = detect_conflicts(agents)

    synthesis = synthesize(
        agents,
        conflict_data,
    )

    return {
        "system": "AletheiaTelos",
        "version": "1.2.0",
        "question": request.question,
        "timestamp": timestamp(),
        "agents": agents,
        "conflicts": conflict_data["conflicts"],
        "horizon_divergences": conflict_data["horizon_divergences"],
        "breaker": {
            "status": "pending",
            "decision": "pending",
            "human_decision_required": True,
        },
        "meta_intelligence": {
            "status": "active",
            "observation": (
                "Independent perspectives contain meaningful "
                "disagreement and should not be reduced to simple averaging."
            ),
        },
        "synthesis": synthesis,
        "governance": {
            "human_decision_required": True,
            "autonomous_execution": False,
            "brokerage_connectivity": False,
        },
    }
