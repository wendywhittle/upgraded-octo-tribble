"""HTTP boundary for research-only outcome calibration."""

from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.calibration import calibrate_predictions


class CalibrationRequest(BaseModel):
    records: List[Dict[str, Any]] = Field(default_factory=list, max_length=10000)
    bins: int = Field(default=5, ge=1, le=20)


def build_calibration_router() -> APIRouter:
    router = APIRouter()

    @router.post("/calibration/evaluate")
    def evaluate(request: CalibrationRequest) -> Dict[str, Any]:
        try:
            return calibrate_predictions(request.records, bins=request.bins)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
