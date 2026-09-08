from datetime import datetime, timedelta, timezone

from app.experiment_001_runner import run_experiment_001_from_csv


def _csv(rows=40):
    header = "observed_at,available_at,source_id,source_version,methodology_version,content_hash,spx_close,vix_close,skew_close"
    start = datetime(2020, 1, 1, tzinfo=timezone.utc)
    data = [header]
    for i in range(rows):
        stamp = (start + timedelta(days=i)).isoformat()
        data.append(f"{stamp},{stamp},fixture,v1,m1,{'a'*64},{3000+i},{15+i/10},{120+i/10}")
    return "\n".join(data)


def test_runner_returns_manifest_identity():
    result = run_experiment_001_from_csv(_csv())
    dataset = result["dataset"]
    assert dataset["point_in_time_validated"] is True
    assert dataset["immutable_input"] is True
    assert len(dataset["content_hash"]) == 64
    assert len(dataset["manifest_fingerprint"]) == 64
