from app.experiment_001_data import HistoricalPoint, build_experiment_observations, validate_points


def _points(count=20):
    points = []
    for i in range(count):
        points.append(
            HistoricalPoint(
                observed_at=f"2025-01-{i + 1:02d}T21:00:00+00:00",
                spx_close=5000 + i * 10,
                vix_level=20 + i * 0.1,
                skew_level=120 + i * 0.2,
                available_at=f"2025-01-{i + 1:02d}T21:00:00+00:00",
                source_id="fixture",
                content_hash=f"hash-{i}",
            )
        )
    return points


def test_builder_uses_only_prior_data_for_features_and_future_data_for_label():
    points = _points()
    observations = build_experiment_observations(points, horizon_days=5)
    first = observations[0]
    assert first.spx_return_5d == points[5].spx_close / points[0].spx_close - 1
    assert first.vix_change_5d == points[5].vix_level / points[0].vix_level - 1
    assert first.skew_change_5d == points[5].skew_level / points[0].skew_level - 1
    expected = min(points[j].spx_close / points[5].spx_close - 1 for j in range(6, 11))
    assert first.future_max_drawdown == expected


def test_point_in_time_violation_is_rejected():
    points = _points()
    points[7] = HistoricalPoint(
        observed_at=points[7].observed_at, spx_close=points[7].spx_close,
        vix_level=points[7].vix_level, skew_level=points[7].skew_level,
        available_at="2025-01-08T22:00:00+00:00", source_id="fixture", content_hash="hash-7",
    )
    try:
        build_experiment_observations(points)
    except ValueError as exc:
        assert "Point-in-time violation" in str(exc)
    else:
        raise AssertionError("Expected point-in-time violation")


def test_missing_provenance_is_rejected():
    points = _points()
    points[3] = HistoricalPoint(
        observed_at=points[3].observed_at, spx_close=points[3].spx_close,
        vix_level=points[3].vix_level, skew_level=points[3].skew_level,
        available_at=points[3].available_at, source_id="", content_hash="hash-3",
    )
    try:
        build_experiment_observations(points)
    except ValueError as exc:
        assert "source_id" in str(exc)
    else:
        raise AssertionError("Expected provenance validation failure")


def test_future_label_is_not_included_as_a_feature():
    points_a = _points()
    points_b = _points()
    points_b[8] = HistoricalPoint(
        observed_at=points_b[8].observed_at, spx_close=4000,
        vix_level=points_b[8].vix_level, skew_level=points_b[8].skew_level,
        available_at=points_b[8].available_at, source_id=points_b[8].source_id,
        content_hash=points_b[8].content_hash,
    )
    first_a = build_experiment_observations(points_a)[0]
    first_b = build_experiment_observations(points_b)[0]
    assert first_a.spx_return_5d == first_b.spx_return_5d
    assert first_a.vix_level == first_b.vix_level
    assert first_a.skew_level == first_b.skew_level
    assert first_a.future_max_drawdown != first_b.future_max_drawdown


def test_timestamps_are_normalized_to_utc_and_timezone_required():
    points = _points()
    points[0] = HistoricalPoint(
        observed_at="2025-01-01T13:00:00-08:00", spx_close=5000,
        vix_level=20, skew_level=120,
        available_at="2025-01-01T13:00:00-08:00", source_id="fixture", content_hash="hash-0",
    )
    validated = validate_points(points)
    assert validated[0].observed_at == "2025-01-01T13:00:00-08:00"

    naive = _points()
    naive[0] = HistoricalPoint(
        observed_at="2025-01-01T21:00:00", spx_close=5000,
        vix_level=20, skew_level=120,
        available_at="2025-01-01T21:00:00+00:00", source_id="fixture", content_hash="hash-0",
    )
    try:
        validate_points(naive)
    except ValueError as exc:
        assert "timezone is required" in str(exc)
    else:
        raise AssertionError("Expected naive timestamp rejection")


def test_equivalent_timezone_instants_are_duplicate_observations():
    points = _points()
    points[1] = HistoricalPoint(
        observed_at="2025-01-01T13:00:00-08:00", spx_close=5010,
        vix_level=20.1, skew_level=120.2,
        available_at="2025-01-01T13:00:00-08:00", source_id="fixture", content_hash="hash-1",
    )
    try:
        validate_points(points)
    except ValueError as exc:
        assert "Duplicate observation timestamp" in str(exc)
    else:
        raise AssertionError("Expected normalized timestamp duplicate rejection")
