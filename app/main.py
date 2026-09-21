from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.deal_flow import STATUSES, build_excel, create_deal, get_deal, list_deals, update_status

app = FastAPI(
    title="AletheiaTelos Deal Flow Engine",
    version="2.0.0",
    description="Real-estate deal intake, deterministic underwriting, records, Excel models, and pipeline.",
)

WEB_DIR = Path(__file__).resolve().parent.parent / "web"


class DealInput(BaseModel):
    name: str = Field(min_length=1)
    asset_type: str = Field(min_length=1)
    location: str = Field(min_length=1)
    purchase_price: float | None = Field(default=None, ge=0)
    noi: float | None = None
    egi: float | None = None
    operating_expenses: float | None = None
    occupancy: float | None = Field(default=None, ge=0, le=1)
    ltv: float | None = Field(default=None, ge=0, le=1)
    interest_rate: float | None = Field(default=None, ge=0)
    amortization_years: float | None = Field(default=None, gt=0)
    hold_years: float | None = Field(default=None, gt=0)
    exit_cap_rate: float | None = Field(default=None, gt=0)
    closing_costs: float | None = Field(default=0, ge=0)
    contact_name: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None


class StatusChange(BaseModel):
    status: str


@app.get("/")
def root() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "product": "deal-flow-engine"}


@app.post("/api/deals")
def submit_deal(deal: DealInput) -> dict[str, Any]:
    return create_deal(deal.model_dump())


@app.get("/api/deals")
def deals() -> list[dict[str, Any]]:
    return list_deals()


@app.get("/api/deals/{deal_id}")
def deal(deal_id: str) -> dict[str, Any]:
    record = get_deal(deal_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return record


@app.patch("/api/deals/{deal_id}/status")
def status(deal_id: str, change: StatusChange) -> dict[str, Any]:
    if change.status not in STATUSES:
        raise HTTPException(status_code=400, detail="Invalid pipeline status")
    record = update_status(deal_id, change.status)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return record


@app.get("/api/deals/{deal_id}/excel")
def excel(deal_id: str) -> Response:
    record = get_deal(deal_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return Response(
        content=build_excel(record),
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{deal_id}.xlsx"'},
    )


@app.get("/web/{asset_path:path}")
def web_asset(asset_path: str) -> FileResponse:
    path = (WEB_DIR / asset_path).resolve()
    if WEB_DIR not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Frontend asset not found")
    return FileResponse(path)
