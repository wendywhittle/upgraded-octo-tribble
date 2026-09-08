from app.experiment_001_runner import run_experiment_001_from_csv


def test_runner_requires_nonempty_csv():
    try:
        run_experiment_001_from_csv("")
    except ValueError:
        assert True
    else:
        assert False
