"""HTTP boundary for the research-only institutional learning report."""

from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.learning import build_learning_report
from app.memory import read_records


class LearningRequest(BaseModel):
    bins: int = Field(default=5, ge=1, le=20)


def build_learning_router() -> APIRouter:
    router = APIRouter()

    @router.post("/observer/learning")
    def learning(request: LearningRequest) -> Dict[str, Any]:
        try:
            return build_learning_report(read_records(), bins=request.bins)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
