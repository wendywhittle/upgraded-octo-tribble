"""FastAPI endpoint for evidence-fed decision-intelligence analysis."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.analysis_pipeline import run_analysis
from app.cre_context import CREOpportunityContext


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    evidence: list[Dict[str, Any]] = Field(default_factory=list, max_length=200)
    initial_value: float = Field(default=100.0, gt=0)
    horizon_steps: int = Field(default=60, ge=1, le=10000)
    paths: int = Field(default=5000, ge=100, le=100000)
    seed: int = Field(default=42, ge=0)
    cre_context: Dict[str, Any] | None = None


def build_analysis_router() -> APIRouter:
    router = APIRouter(prefix="/analysis", tags=["decision-intelligence"])

    @router.post("/run")
    def analyze(request: AnalysisRequest) -> Dict[str, Any]:
        try:
            cre_context = CREOpportunityContext(**request.cre_context) if request.cre_context else None
            return run_analysis(
                question=request.question,
                evidence=request.evidence,
                initial_value=request.initial_value,
                horizon_steps=request.horizon_steps,
                paths=request.paths,
                seed=request.seed,
                cre_context=cre_context,
            )
        except (TypeError, ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
