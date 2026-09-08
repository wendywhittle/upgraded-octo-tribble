"""HTTP boundary for research-only forecast resolution."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.memory import append_record, read_records
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

    return router
