from app.experiment_001_uncertainty import metric_differences, moving_block_bootstrap


def _fixture(n=40):
    y = [0 if i % 3 else 1 for i in range(n)]
    baseline = [0.20 + 0.01 * (i % 5) for i in range(n)]
    augmented = [min(0.95, p + (0.08 if target else -0.01)) for p, target in zip(baseline, y)]
    return y, baseline, augmented


def test_metric_differences_are_deterministic():
    y, baseline, augmented = _fixture()
    first = metric_differences(y, baseline, augmented)
    second = metric_differences(y, baseline, augmented)
    assert first == second
    assert set(first) == {"brier_improvement", "log_loss_improvement", "auc_improvement"}


def test_moving_block_bootstrap_is_reproducible_and_reports_intervals():
    y, baseline, augmented = _fixture()
    first = moving_block_bootstrap(y, baseline, augmented, block_length=5, resamples=300, seed=7)
    second = moving_block_bootstrap(y, baseline, augmented, block_length=5, resamples=300, seed=7)
    assert [item.as_dict() for item in first] == [item.as_dict() for item in second]
    assert {item.metric for item in first} == {
        "brier_improvement",
        "log_loss_improvement",
        "auc_improvement",
    }
    assert all(item.lower <= item.estimate <= item.upper for item in first)
    assert all(item.block_length == 5 for item in first)


def test_uncertainty_rejects_single_class_evaluation():
    y = [1] * 20
    baseline = [0.5] * 20
    augmented = [0.6] * 20
    try:
        moving_block_bootstrap(y, baseline, augmented, resamples=100)
    except ValueError as exc:
        assert "both classes" in str(exc)
    else:
        raise AssertionError("single-class uncertainty analysis must fail closed")
