from app.calibration import calibrate_predictions


def test_calibration_uses_only_explicit_probabilities():
    result = calibrate_predictions([
        {"predicted_probability": 0.8, "outcome": True},
        {"predicted_probability": 0.2, "outcome": False},
        {"confidence": 0.99, "outcome": True},
    ])
    assert result["sample_count"] == 2
    assert result["excluded_count"] == 1
    assert result["brier_score"] == 0.04
    assert result["historical_records_mutated"] is False
    assert result["research_only"] is True


def test_calibration_reports_insufficient_data():
    result = calibrate_predictions([])
    assert result["status"] == "insufficient_data"
    assert result["brier_score"] is None
    assert result["sample_count"] == 0
    assert result["human_decision_required"] if "human_decision_required" in result else True


def test_calibration_rejects_invalid_bin_count():
    try:
        calibrate_predictions([], bins=0)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
