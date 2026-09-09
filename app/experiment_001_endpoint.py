"""HTTP boundary for running Experiment #001 on authorized CSV data."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from .experiment_001_runner import run_experiment_001_from_csv


class Experiment001Request(BaseModel):
    csv_text: str = Field(min_length=1, description="Authorized EXP-001 canonical CSV payload")


def build_experiment_001_router() -> APIRouter:
    router = APIRouter(tags=["experiments"])

    @router.post("/experiments/EXP-001/run")
    def run_experiment(request: Experiment001Request) -> Dict[str, Any]:
        try:
            return run_experiment_001_from_csv(request.csv_text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router


__all__ = ["Experiment001Request", "build_experiment_001_router"]
