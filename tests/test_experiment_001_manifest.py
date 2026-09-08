from app.experiment_001_manifest import build_dataset_manifest, fingerprint_rows


def _kwargs():
    return {
        "dataset_id": "EXP001-SAMPLE-001",
        "source_id": "licensed-provider-export",
        "source_version": "2026-09",
        "methodology_version": "cboe-skew-methodology-v1",
        "schema_version": "exp001-1",
        "content_hash": "a" * 64,
        "observation_start": "2010-01-04",
        "observation_end": "2020-12-31",
        "row_count": 2500,
    }


def test_manifest_requires_point_in_time_data():
    values = _kwargs()
    values["point_in_time"] = False
    try:
        build_dataset_manifest(**values)
    except ValueError as exc:
        assert "point-in-time" in str(exc)
    else:
        raise AssertionError("non-point-in-time dataset must be rejected")


def test_manifest_requires_methodology_version():
    values = _kwargs()
    values["methodology_version"] = ""
    try:
        build_dataset_manifest(**values)
    except ValueError as exc:
        assert "methodology_version" in str(exc)
    else:
        raise AssertionError("methodology version must be required")


def test_manifest_fingerprint_is_stable():
    first = build_dataset_manifest(**_kwargs())
    second = build_dataset_manifest(**_kwargs())
    assert first.fingerprint() == second.fingerprint()


def test_manifest_fingerprint_changes_when_dataset_identity_changes():
    first = build_dataset_manifest(**_kwargs())
    values = _kwargs()
    values["content_hash"] = "b" * 64
    second = build_dataset_manifest(**values)
    assert first.fingerprint() != second.fingerprint()


def test_row_fingerprint_is_order_sensitive_for_source_rows():
    rows = [{"observed_at": "2020-01-02", "spx_close": 100}, {"observed_at": "2020-01-03", "spx_close": 101}]
    assert fingerprint_rows(rows) != fingerprint_rows(list(reversed(rows)))


def test_manifest_is_research_only_by_design():
    manifest = build_dataset_manifest(**_kwargs())
    assert manifest.point_in_time is True
