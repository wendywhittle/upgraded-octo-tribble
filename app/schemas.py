from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


Direction = Literal["LONG", "SHORT", "NEUTRAL", "NO_DATA"]
ScenarioName = Literal["base", "bull", "bear", "adversarial", "tail_risk"]
ConflictType = Literal[
    "factual", "evidentiary", "statistical", "methodological", "interpretive",
    "assumption", "scenario", "horizon", "uncertainty",
]


class Evidence(BaseModel):
    evidence_id: str
    source: str
    claim: str
    observed_at: Optional[str] = None
    retrieved_at: Optional[str] = None
    freshness_seconds: Optional[float] = None
    provenance: Optional[Dict[str, Any]] = None


class AgentOutput(BaseModel):
    agent_id: str
    strategy: str
    direction: Direction
    confidence: float = Field(ge=0.0, le=1.0)
    horizon: str
    evidence: List[Evidence] = Field(default_factory=list)
    evidence_basis: List[str] = Field(default_factory=list)
    contradictory_evidence: List[Evidence] = Field(default_factory=list)
    contradictory_evidence_basis: List[str] = Field(default_factory=list)
    invalidation_conditions: List[str] = Field(default_factory=list)
    data_timestamp: Optional[str] = None
    model_version: str
    regime_assumption: Optional[str] = None
    capacity_constraint: Optional[str] = None
    assumptions: List[str] = Field(default_factory=list)
    predicted_probability: Optional[float] = Field(default=None, ge=0.0, le=1.0)
    prediction_id: Optional[str] = None


class ConflictRecord(BaseModel):
    proposition: str
    conflict_type: ConflictType
    perspectives: List[str] = Field(min_length=2)
    supporting_evidence: List[str] = Field(default_factory=list)
    contradicting_evidence: List[str] = Field(default_factory=list)
    assumption_conflicts: List[Dict[str, Any]] = Field(default_factory=list)
    unresolved_questions: List[str] = Field(default_factory=list)
    severity: Literal["moderate", "material"]
    status: Literal["unresolved", "resolved"]


class SimulationRequest(BaseModel):
    question: str
    initial_value: float = Field(default=100.0, gt=0)
    horizon_steps: int = Field(default=60, ge=1, le=1000)
    paths: int = Field(default=5000, ge=100, le=100000)
    seed: int = 42


class ScenarioSummary(BaseModel):
    scenario: ScenarioName
    mean_terminal: float
    median_terminal: float
    p05_terminal: float
    p95_terminal: float
    probability_loss: float
    max_drawdown_mean: float


class SimulationResult(BaseModel):
    engine: str
    independent_of_agents: bool
    paths: int
    horizon_steps: int
    seed: int
    scenarios: List[ScenarioSummary]
    assumptions: List[str]


class SkepticReview(BaseModel):
    status: Literal["reviewed", "blocked", "insufficient_data"]
    challenge_count: int
    challenges: List[str]
    recommendation: Literal["proceed_to_synthesis", "hold", "no_data"]
