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


def test_default_spec_matches_preregistered_hypothesis():
    spec = Experiment001Spec()
    assert spec.horizon_days == 5
    assert spec.drawdown_threshold == -0.03
    assert "vix_level" in spec.baseline_features
    assert "skew_level" in spec.incremental_features
