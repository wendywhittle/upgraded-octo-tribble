from pathlib import Path
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, Response
from pydantic import BaseModel, Field

from app import evidence as evidence_mod
from app import journal as journal_mod
from app import perspectives as perspectives_mod
from app import scenarios as scenarios_mod
from app import simulation as simulation_mod
from app.deal_flow import STATUSES, build_excel, connect, create_deal, get_deal, list_deals, update_status
from app.schema import migrate

# Charter §7 financial boundary: this service is analysis and workflow
# support only. It must never connect to a brokerage, hold trading
# credentials, place orders, or move capital. No such code belongs here.
migrate()

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


# ---------------------------------------------------------------------------
# Charter-aligned capabilities: evidence, perspectives, scenarios, simulation,
# decision journal, observer. Analysis only; see the §7 note at the top.
# ---------------------------------------------------------------------------

def _require_deal(deal_id: str) -> dict[str, Any]:
    record = get_deal(deal_id)
    if not record:
        raise HTTPException(status_code=404, detail="Deal not found")
    return record


class EvidenceIn(BaseModel):
    type: str
    source: str | None = None
    content: str


@app.post("/api/deals/{deal_id}/evidence")
def add_evidence(deal_id: str, item: EvidenceIn) -> dict[str, Any]:
    _require_deal(deal_id)
    conn = connect()
    try:
        try:
            return evidence_mod.add_evidence(conn, deal_id, item.type, item.content, item.source)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.get("/api/deals/{deal_id}/evidence")
def get_evidence(deal_id: str) -> list[dict[str, Any]]:
    _require_deal(deal_id)
    conn = connect()
    try:
        return evidence_mod.list_evidence(conn, deal_id)
    finally:
        conn.close()


class PerspectivesIn(BaseModel):
    lenses: list[str] | None = None


@app.post("/api/deals/{deal_id}/perspectives")
def run_perspectives(deal_id: str, body: PerspectivesIn) -> list[dict[str, Any]]:
    record = _require_deal(deal_id)
    conn = connect()
    try:
        items = evidence_mod.list_evidence(conn, deal_id)
        try:
            analyses = perspectives_mod.analyze_deal(record, items, body.lenses)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return perspectives_mod.save_perspectives(conn, deal_id, analyses)
    finally:
        conn.close()


@app.get("/api/deals/{deal_id}/perspectives")
def get_perspectives(deal_id: str) -> list[dict[str, Any]]:
    _require_deal(deal_id)
    conn = connect()
    try:
        return perspectives_mod.list_perspectives(conn, deal_id)
    finally:
        conn.close()


class ScenarioDef(BaseModel):
    name: str
    overrides: dict[str, Any] = {}
    notes: str = ""


class ScenariosIn(BaseModel):
    scenarios: list[ScenarioDef] | None = None


@app.post("/api/deals/{deal_id}/scenarios")
def run_scenarios(deal_id: str, body: ScenariosIn) -> list[dict[str, Any]]:
    record = _require_deal(deal_id)
    conn = connect()
    try:
        defs = None if body.scenarios is None else [s.model_dump() for s in body.scenarios]
        try:
            results = scenarios_mod.run_scenarios(record["original_inputs"], defs)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return scenarios_mod.save_scenarios(conn, deal_id, results)
    finally:
        conn.close()


@app.get("/api/deals/{deal_id}/scenarios")
def get_scenarios(deal_id: str) -> list[dict[str, Any]]:
    _require_deal(deal_id)
    conn = connect()
    try:
        return scenarios_mod.list_scenarios(conn, deal_id)
    finally:
        conn.close()


class SimulateIn(BaseModel):
    ranges: dict[str, list[float]]
    n: int = 1000
    seed: int = 0


@app.post("/api/deals/{deal_id}/simulate")
def run_simulation(deal_id: str, body: SimulateIn) -> dict[str, Any]:
    record = _require_deal(deal_id)
    conn = connect()
    try:
        try:
            summary = simulation_mod.simulate(record["original_inputs"], body.ranges, body.n, body.seed)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        return simulation_mod.save_simulation(
            conn, deal_id,
            {"ranges": body.ranges, "n": body.n, "seed": body.seed}, summary,
        )
    finally:
        conn.close()


@app.get("/api/deals/{deal_id}/simulations")
def get_simulations(deal_id: str) -> list[dict[str, Any]]:
    _require_deal(deal_id)
    conn = connect()
    try:
        return simulation_mod.list_simulations(conn, deal_id)
    finally:
        conn.close()


class ThesisIn(BaseModel):
    thesis: str
    key_assumptions: list[str] = []
    expected_outcome: str | None = None


@app.post("/api/deals/{deal_id}/thesis")
def add_thesis(deal_id: str, body: ThesisIn) -> dict[str, Any]:
    _require_deal(deal_id)
    conn = connect()
    try:
        try:
            return journal_mod.record_thesis(
                conn, deal_id, body.thesis, body.key_assumptions, body.expected_outcome
            )
        except KeyError as e:
            raise HTTPException(status_code=404, detail=str(e))
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.get("/api/deals/{deal_id}/thesis")
def get_thesis(deal_id: str) -> list[dict[str, Any]]:
    _require_deal(deal_id)
    conn = connect()
    try:
        return journal_mod.list_theses(conn, deal_id)
    finally:
        conn.close()


class OutcomeIn(BaseModel):
    actual_outcome: str
    lesson: str | None = None


@app.post("/api/deals/{deal_id}/outcome")
def add_outcome(deal_id: str, body: OutcomeIn) -> dict[str, Any]:
    _require_deal(deal_id)
    conn = connect()
    try:
        try:
            return journal_mod.record_outcome(conn, deal_id, body.actual_outcome, body.lesson)
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
    finally:
        conn.close()


@app.get("/api/observer")
def observer() -> dict[str, Any]:
    conn = connect()
    try:
        return journal_mod.observer_summary(conn)
    finally:
        conn.close()
