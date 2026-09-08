from app.experiment_001_runner import run_experiment_001_from_csv


def test_runner_rejects_empty_input():
    try:
        run_experiment_001_from_csv("")
    except ValueError:
        return
    raise AssertionError("empty input must be rejected")
