from pathlib import Path
from typing import Any
import hashlib
import hmac
import os

from fastapi import Cookie, Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.deal_flow import STATUSES, build_excel, create_deal, get_deal, list_deals, update_status

app = FastAPI(
    title="AletheiaTelos Deal Flow Engine",
    version="2.1.0",
    description="Public deal intake with protected internal deal processing.",
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


def access_key() -> str:
    return os.getenv("ALETHEIA_INTERNAL_ACCESS_KEY", "")


def session_token() -> str:
    key = access_key()
    if not key:
        return ""
    return hmac.new(key.encode(), b"aletheiatelos-internal-session", hashlib.sha256).hexdigest()


def require_internal_session(
    request: Request,
    internal_session: str | None = Cookie(default=None),
) -> None:
    expected = session_token()
    bearer = request.headers.get("authorization", "")
    presented = internal_session
    if bearer.lower().startswith("bearer "):
        presented = bearer[7:].strip()
    if not expected or not presented or not hmac.compare_digest(presented, expected):
        raise HTTPException(status_code=401, detail="Internal access required")


@app.get("/")
def root() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/internal")
def internal() -> FileResponse:
    return FileResponse(WEB_DIR / "internal.html")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "product": "deal-flow-engine"}


@app.post("/internal/login")
def internal_login(request: Request, payload: dict[str, str]) -> Response:
    key = access_key()
    if not key or not hmac.compare_digest(str(payload.get("access_key", "")).strip(), key.strip()):
        raise HTTPException(status_code=401, detail="Access denied")
    token = session_token()
    response = Response(
        content='{"authenticated":true,"token":"' + token + '"}',
        media_type="application/json",
    )
    response.set_cookie(
        "internal_session",
        token,
        httponly=True,
        secure=request.url.scheme == "https",
        samesite="strict",
        max_age=28800,
        path="/",
    )
    return response


@app.get("/internal/session")
def internal_session(_: None = Depends(require_internal_session)) -> dict[str, bool]:
    return {"authenticated": True}


@app.post("/internal/logout")
def internal_logout() -> Response:
    response = Response(content='{"authenticated":false}', media_type="application/json")
    response.delete_cookie("internal_session", path="/")
    return response


@app.post("/api/deals")
def submit_deal(deal: DealInput) -> dict[str, Any]:
    return create_deal(deal.model_dump())


@app.get("/api/deals")
def deals(_: None = Depends(require_internal_session)) -> list[dict[str, Any]]:
    return list_deals()


@app.get("/api/deals/{deal_id}")
def deal(deal_id: str, _: None = Depends(require_internal_session)) -> dict[str, Any]:
    record = get_deal(deal_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return record


@app.patch("/api/deals/{deal_id}/status")
def status(deal_id: str, change: StatusChange, _: None = Depends(require_internal_session)) -> dict[str, Any]:
    if change.status not in STATUSES:
        raise HTTPException(status_code=400, detail="Invalid pipeline status")
    record = update_status(deal_id, change.status)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return record


@app.get("/api/deals/{deal_id}/excel")
def excel(deal_id: str, _: None = Depends(require_internal_session)) -> Response:
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
