from typing import Any, Dict

from fastapi import APIRouter

from app.external_capital import DEFAULT_EXTERNAL_CAPITAL_REGISTRY


def build_external_capital_router() -> APIRouter:
    """Build the read-only external-capital ecosystem router."""
    router = APIRouter(prefix="/external-capital", tags=["external-capital"])

    @router.get("/manifest")
    def manifest() -> Dict[str, Any]:
        return DEFAULT_EXTERNAL_CAPITAL_REGISTRY.manifest()

    return router
