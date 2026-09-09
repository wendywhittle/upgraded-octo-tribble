import pytest

from app.experiment_001 import Observation, evaluate_experiment_001


def _single_class_observations():
    return [
        Observation(
            observed_at=f"2020-01-{i + 1:02d}",
            spx_return_5d=0.001 * i,
            vix_level=18.0,
            vix_change_5d=0.0,
            skew_level=120.0,
            skew_change_5d=0.0,
            future_max_drawdown=-0.005,
        )
        for i in range(40)
    ]


def test_training_single_class_is_rejected():
    with pytest.raises(ValueError, match="training window"):
        evaluate_experiment_001(_single_class_observations())
