from app.analysis_endpoint import AnalysisRequest, build_analysis_router


def test_analysis_request_defaults_are_bounded():
    request = AnalysisRequest(question="Assess the opportunity")
    assert request.paths == 5000
    assert request.horizon_steps == 60
    assert request.seed == 42


def test_analysis_router_exposes_run_route():
    router = build_analysis_router()
    paths = {route.path for route in router.routes}
    assert "/analysis/run" in paths
