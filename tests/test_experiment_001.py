from app.experiment_001 import Experiment001Spec, Observation, evaluate_experiment_001


def _observations():
    rows = []
    for i in range(40):
        # Deterministic synthetic fixture only: it tests mechanics, not the
        # empirical SKEW hypothesis. Real historical data must replace it.
        skew = 115 + (i % 8) * 2
        event = i >= 28 and i % 3 == 0
        drawdown = -0.04 if event else -0.005
        rows.append(
            Observation(
                observed_at=f"2020-01-{i + 1:02d}",
                spx_return_5d=-0.01 + (i % 5) * 0.002,
                vix_level=16 + (i % 7),
                vix_change_5d=(i % 4 - 1) * 0.4,
                skew_level=skew,
                skew_change_5d=2.0 if event else -0.5,
                future_max_drawdown=drawdown,
            )
        )
    return rows


def test_experiment_is_chronological_and_research_only():
    result = evaluate_experiment_001(_observations())
    assert result["experiment_id"] == "EXP-001"
    assert result["specification"]["chronological_split"] is True
    assert result["specification"]["point_in_time_required"] is True
    assert result["governance"]["research_only"] is True
    assert result["governance"]["execution_capability"] is False
    assert result["governance"]["brokerage_connectivity"] is False
    assert result["governance"]["portfolio_mutation"] is False


def test_incremental_comparison_reports_all_predeclared_metrics():
    result = evaluate_experiment_001(_observations())
    assert set(result["incremental"]) == {
        "brier_improvement",
        "log_loss_improvement",
        "auc_improvement",
    }
    assert result["baseline"]["sample_count"] == result["augmented"]["sample_count"]


def test_dataset_diagnostics_report_both_classes_in_each_window():
    result = evaluate_experiment_001(_observations())
    diagnostics = result["dataset_diagnostics"]
    assert diagnostics["total_observations"] == 40
    assert diagnostics["training_observations"] == 28
    assert diagnostics["test_observations"] == 12
    assert diagnostics["training_positive_events"] > 0
    assert diagnostics["training_negative_events"] > 0
    assert diagnostics["test_positive_events"] > 0
    assert diagnostics["test_negative_events"] > 0
    assert 0.0 < diagnostics["test_positive_rate"] < 1.0


def test_default_spec_matches_preregistered_hypothesis():
    spec = Experiment001Spec()
    assert spec.horizon_days == 5
    assert spec.drawdown_threshold == -0.03
    assert "vix_level" in spec.baseline_features
    assert "skew_level" in spec.incremental_features


def test_single_class_test_window_is_rejected():
    observations = _observations()
    for item in observations[28:]:
        item_index = observations.index(item)
        observations[item_index] = Observation(
            observed_at=item.observed_at,
            spx_return_5d=item.spx_return_5d,
            vix_level=item.vix_level,
            vix_change_5d=item.vix_change_5d,
            skew_level=item.skew_level,
            skew_change_5d=item.skew_change_5d,
            future_max_drawdown=-0.005,
        )
    try:
        evaluate_experiment_001(observations)
    except ValueError as exc:
        assert "test window" in str(exc)
    else:
        raise AssertionError("Expected single-class test window to be rejected")
