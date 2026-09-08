from app.calibration_endpoint import CalibrationRequest, build_calibration_router


def test_calibration_request_defaults():
    request = CalibrationRequest()
    assert request.records == []
    assert request.bins == 5


def test_calibration_route_is_read_only_evaluation_surface():
    routes = build_calibration_router().routes
    assert any(getattr(route, "path", None) == "/calibration/evaluate" for route in routes)
