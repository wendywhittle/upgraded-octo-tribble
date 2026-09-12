from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

from app.analysis_endpoint import build_analysis_router
from app.analysis_pipeline import detect_conflicts, run_analysis, synthesize
from app.calibration_endpoint import build_calibration_router
from app.capital_endpoint import build_capital_router
from app.cre_endpoint import build_cre_router
from app.config import live_market_enabled, market_symbol_map, research_feed_urls
from app.experiment_001_endpoint import Experiment001Request, build_experiment_001_router
from app.experiment_001_runner import run_experiment_001_from_csv
from app.learning import build_learning_report
from app.learning_endpoint import LearningRequest, build_learning_router
from app.live_market_endpoint import build_live_market_router
from app.memory import append_record, read_records
from app.prediction_resolution import resolve_prediction
from app.prediction_resolution_endpoint import PredictionResolutionRequest, build_prediction_resolution_router
from app.research_endpoint import build_research_router
from app.schemas import SimulationRequest

app = FastAPI(title="AletheiaTelos", version="1.12.0", description="Research and decision intelligence system; not an autonomous trading system.")
WEB_DIR = Path(__file__).resolve().parent.parent / "web"


def timestamp() -> str:
    return datetime.now(timezone.utc).isoformat()


app.include_router(build_analysis_router())
app.include_router(build_calibration_router())
app.include_router(build_capital_router())
app.include_router(build_cre_router())
app.include_router(build_prediction_resolution_router())
app.include_router(build_learning_router())
app.include_router(build_experiment_001_router())

# Explicit application-boundary fallbacks keep the public routes observable even if
# router composition is altered by a future integration refactor.
if not any(getattr(route, "path", None) == "/observer/learning" for route in app.routes):
    @app.post("/observer/learning")
    def observer_learning(request: LearningRequest) -> Dict[str, Any]:
        return build_learning_report(read_records(), bins=request.bins)

if not any(getattr(route, "path", None) == "/predictions/resolve" for route in app.routes):
    @app.post("/predictions/resolve")
    def resolve_prediction_route(request: PredictionResolutionRequest) -> Dict[str, Any]:
        prediction_id = request.prediction.get("prediction_id")
        if any(
            record.get("record_type") == "prediction_resolution"
            and record.get("prediction_id") == prediction_id
            for record in read_records()
        ):
            raise HTTPException(status_code=409, detail="prediction_id has already been resolved")
        try:
            result = resolve_prediction(
                request.prediction,
                request.outcome,
                request.resolved_at,
                request.outcome_source,
            )
            append_record(result)
            return result
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

if not any(getattr(route, "path", None) == "/experiments/EXP-001/run" for route in app.routes):
    @app.post("/experiments/EXP-001/run", tags=["experiments"])
    def run_experiment_001_route(request: Experiment001Request) -> Dict[str, Any]:
        try:
            return run_experiment_001_from_csv(request.csv_text)
        except ValueError as exc:
            raise HTTPException(status_code=400, detail=str(exc)) from exc

@app.get("/")
def root():
    return FileResponse(WEB_DIR / "index.html")


@app.get("/health")
def health():
    return {"status": "healthy", "timestamp": timestamp(), "live_market_data": live_market_enabled()}


@app.get("/memory")
def memory():
    records = read_records()
    return {"count": len(records), "records": records}


@app.get("/web/{asset_path:path}")
def web_asset(asset_path: str):
    path = (WEB_DIR / asset_path).resolve()
    if WEB_DIR not in path.parents or not path.is_file():
        raise HTTPException(status_code=404, detail="Frontend asset not found")
    return FileResponse(path)


feed_urls = research_feed_urls()
if feed_urls:
    app.include_router(build_research_router(feed_urls))

if live_market_enabled():
    app.include_router(build_live_market_router(market_symbol_map()))


@app.post("/simulate")
def simulate(request: SimulationRequest):
    """Compatibility route delegating to the canonical analysis pipeline."""
    result = run_analysis(
        question=request.question,
        evidence=[],
        initial_value=request.initial_value,
        horizon_steps=request.horizon_steps,
        paths=request.paths,
        seed=request.seed,
    )
    result["version"] = "1.12.0"
    result["timestamp"] = timestamp()
    result["breaker"] = {"status": "pending", "decision": "pending", "human_decision_required": True}
    result["meta_intelligence"] = {"status": "active", "observation": "Independent perspectives and simulation distributions remain separately inspectable."}
    return result
