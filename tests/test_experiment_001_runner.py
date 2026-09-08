from datetime import datetime, timedelta, timezone

from app.experiment_001_runner import run_experiment_001_from_csv


def _csv(rows=40):
    lines = [
        "observed_at,available_at,source_id,source_version,methodology_version,content_hash,spx_close,vix_close,skew_close"
    ]
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    for i in range(rows):
        stamp = (start + timedelta(days=i)).isoformat()
        lines.append(
            f"{stamp},{stamp},fixture,v1,m1,{'a'*64},{3000+i},{15+i/10},{120+i/10}"
        )
    return "\n".join(lines)


def test_runner_rejects_mixed_provenance():
    csv = _csv().replace(",fixture,v1,m1,", ",other,v1,m1,", 1)
    try:
        run_experiment_001_from_csv(csv)
    except ValueError as exc:
        assert "one source_id" in str(exc)
    else:
        raise AssertionError("mixed provenance must be rejected")


def test_runner_builds_immutable_dataset_identity():
    result = run_experiment_001_from_csv(_csv())
    dataset = result["dataset"]
    assert dataset["point_in_time_validated"] is True
    assert dataset["immutable_input"] is True
    assert len(dataset["content_hash"]) == 64
    assert len(dataset["manifest_fingerprint"]) == 64
    assert dataset["manifest"]["schema_version"] == "EXP-001-CANONICAL-CSV-v1"
