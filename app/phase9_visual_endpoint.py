"""HTTP boundary for observing the Phase 9 investment case pipeline."""
from fastapi import APIRouter
from pydantic import BaseModel

from app.phase9_visual import Phase9VisualRequest, assemble_visual_case

router = APIRouter(prefix="/phase9", tags=["phase9-visual"])


class Phase9VisualResponse(BaseModel):
    assembly: dict
    governance: dict
    visual_integration: dict


@router.post("/visual", response_model=Phase9VisualResponse)
def run_phase9_visual(request: Phase9VisualRequest) -> Phase9VisualResponse:
    """Observe a Phase 9 assembly without exposing authorization or workflow mutation."""
    return Phase9VisualResponse(**assemble_visual_case(request))
