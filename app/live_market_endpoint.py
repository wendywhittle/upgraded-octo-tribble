"""FastAPI route factory for explicitly enabled live market research."""

from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.live_market_research import live_market_research
from app.stooq_market_data import StooqMarketDataSource


class LiveMarketRequest(BaseModel):
    symbols: list[str] = Field(min_length=1, max_length=20)


def build_live_market_router(symbol_map: dict[str, str] | None = None) -> APIRouter:
    router = APIRouter(prefix="/market", tags=["market-research"])
    source = StooqMarketDataSource(symbol_map=symbol_map)

    @router.post("/research")
    def research(request: LiveMarketRequest) -> Dict[str, Any]:
        try:
            return live_market_research(source, request.symbols)
        except (ValueError, RuntimeError, OSError) as exc:
            raise HTTPException(status_code=502, detail=str(exc)) from exc

    return router
