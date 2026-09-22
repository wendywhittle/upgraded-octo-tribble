from pathlib import Path
from typing import Any, Annotated

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app.auth import (
    InternalSession,
    clear_session_cookie,
    login,
    login_page,
    login_response,
    read_session,
    require_csrf,
    require_internal_operator,
    unauthorized_internal_redirect,
)

from app.deal_flow import STATUSES, build_excel, create_deal, get_deal, list_deals, update_status

app = FastAPI(
    title="AletheiaTelos Deal Flow Engine",
    version="2.1.0",
    description="Public deal intake with internal deal processing.",
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


class LoginInput(BaseModel):
    username: str
    password: str


def require_internal_mutation(
    request: Request,
    session: Annotated[InternalSession, Depends(require_internal_operator)],
) -> InternalSession:
    require_csrf(request, session)
    return session


@app.get("/")
def root() -> FileResponse:
    return FileResponse(WEB_DIR / "index.html")


@app.get("/internal")
def internal(request: Request) -> Response:
    if read_session(request) is None:
        return unauthorized_internal_redirect()
    return FileResponse(WEB_DIR / "internal.html")


@app.get("/internal/login")
def internal_login() -> Response:
    return login_page()


@app.post("/internal/login")
def internal_login_submit(credentials: LoginInput) -> Response:
    try:
        token = login(credentials.username, credentials.password)
    except PermissionError:
        raise HTTPException(status_code=429, detail="Authentication temporarily unavailable")
    except (ValueError, RuntimeError):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    return login_response(token)


@app.post("/internal/logout")
def internal_logout() -> Response:
    response = Response(status_code=204)
    clear_session_cookie(response)
    return response


@app.get("/api/internal/session")
def internal_session(
    session: Annotated[InternalSession, Depends(require_internal_operator)],
) -> dict[str, Any]:
    return {
        "authenticated": True,
        "username": session.username,
        "role": session.role,
        "csrf_token": session.csrf_token,
        "expires_at": session.expires_at,
    }


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "healthy", "product": "deal-flow-engine"}


@app.post("/api/deals")
def submit_deal(deal: DealInput) -> dict[str, Any]:
    return create_deal(deal.model_dump())


@app.get("/api/deals")
def deals(
    _: Annotated[InternalSession, Depends(require_internal_operator)],
) -> list[dict[str, Any]]:
    return list_deals()


@app.get("/api/deals/{deal_id}")
def deal(
    deal_id: str,
    _: Annotated[InternalSession, Depends(require_internal_operator)],
) -> dict[str, Any]:
    record = get_deal(deal_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return record


@app.patch("/api/deals/{deal_id}/status")
def status(
    deal_id: str,
    change: StatusChange,
    _: Annotated[InternalSession, Depends(require_internal_mutation)],
) -> dict[str, Any]:
    if change.status not in STATUSES:
        raise HTTPException(status_code=400, detail="Invalid pipeline status")
    record = update_status(deal_id, change.status)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return record


@app.get("/api/deals/{deal_id}/excel")
def excel(
    deal_id: str,
    _: Annotated[InternalSession, Depends(require_internal_operator)],
) -> Response:
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
