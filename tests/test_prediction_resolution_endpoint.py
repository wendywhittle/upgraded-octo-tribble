from app.prediction_resolution_endpoint import PredictionResolutionRequest, build_prediction_resolution_router


def test_resolution_endpoint_contract():
    request = PredictionResolutionRequest(
        prediction={"prediction_id": "pred-x", "predicted_probability": 0.7},
        outcome=True,
        resolved_at="2026-09-09T12:00:00+00:00",
    )
    assert request.outcome is True
    assert "/predictions/resolve" in [route.path for route in build_prediction_resolution_router().routes]
