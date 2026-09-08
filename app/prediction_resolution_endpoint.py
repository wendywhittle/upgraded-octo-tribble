"""HTTP boundary for research-only forecast resolution."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.prediction_resolution import resolve_prediction


class PredictionResolutionRequest(BaseModel):
    prediction: Dict[str, Any]
    outcome: bool
    resolved_at: str = Field(min_length=1)
    outcome_source: str | None = None


def build_prediction_resolution_router() -> APIRouter:
    router = APIRouter()

    @router.post("/predictions/resolve")
    def resolve(request: PredictionResolutionRequest) -> Dict[str, Any]:
        try:
            return resolve_prediction(
                request.prediction,
                request.outcome,
                request.resolved_at,
                request.outcome_source,
            )
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
