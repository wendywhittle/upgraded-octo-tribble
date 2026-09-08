"""FastAPI route factory for explicitly configured read-only research sources."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.research import research_query
from app.rss_adapter import RSSFeedEvidenceSource


class ResearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=500)
    claim: str = Field(min_length=1, max_length=2000)
    limit: int = Field(default=10, ge=1, le=50)


def build_research_router(feed_urls: list[str]) -> APIRouter:
    router = APIRouter(prefix="/research", tags=["research"])
    source = RSSFeedEvidenceSource(feed_urls)

    @router.post("/evidence")
    def evidence(request: ResearchRequest) -> Dict[str, Any]:
        try:
            return research_query(
                source,
                query=request.query,
                claim=request.claim,
                limit=request.limit,
            )
        except (ValueError, RuntimeError) as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

    return router
