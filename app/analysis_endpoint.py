"""FastAPI endpoint for evidence-fed decision-intelligence analysis."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.analysis_pipeline import run_analysis


class AnalysisRequest(BaseModel):
    question: str = Field(min_length=1, max_length=2000)
    evidence: list[Dict[str, Any]] = Field(default_factory=list, max_length=200)
    initial_value: float = Field(default=100.0, gt=0)
    horizon_steps: int = Field(default=60, ge=1, le=10000)
    paths: int = Field(default=5000, ge=100, le=100000)
    seed: int = Field(default=42, ge=0)
    asset: str = Field(default="", max_length=500)
    market: str = Field(default="", max_length=500)


def build_analysis_router() -> APIRouter:
    router = APIRouter(prefix="/analysis", tags=["decision-intelligence"])

    @router.post("/run")
    def analyze(request: AnalysisRequest) -> Dict[str, Any]:
        try:
            research_context = {
                "asset": request.asset.strip(),
                "market": request.market.strip(),
            }
            research_context = {key: value for key, value in research_context.items() if value}
            return run_analysis(
                question=request.question,
                evidence=request.evidence,
                initial_value=request.initial_value,
                horizon_steps=request.horizon_steps,
                paths=request.paths,
                seed=request.seed,
                research_context=research_context,
            )
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
