from app.experiment_001_csv import dataset_content_hash, parse_csv


HEADER = "observed_at,available_at,source_id,source_version,methodology_version,content_hash,spx_close,vix_close,skew_close"


def row(day: str, skew: float = 130.0) -> str:
    return f"{day}T21:00:00+00:00,{day}T21:00:00+00:00,licensed-source,v1,skew-method-v1,abc123,5000,15,{skew}"


def test_valid_csv_is_point_in_time_and_reproducible():
    text = HEADER + "\n" + row("2024-01-02") + "\n" + row("2024-01-03") + "\n"
    rows = parse_csv(text)
    assert len(rows) == 2
    assert dataset_content_hash(rows) == dataset_content_hash(parse_csv(text))


def test_future_available_at_is_rejected():
    text = HEADER + "\n" + "2024-01-02T21:00:00+00:00,2024-01-03T21:00:00+00:00,licensed-source,v1,skew-method-v1,abc123,5000,15,130\n"
    try:
        parse_csv(text)
    except ValueError as exc:
        assert "point-in-time" in str(exc)
    else:
        raise AssertionError("future availability must be rejected")


def test_duplicate_observation_is_rejected():
    text = HEADER + "\n" + row("2024-01-02") + "\n" + row("2024-01-02", 131) + "\n"
    try:
        parse_csv(text)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("duplicate observations must be rejected")


def test_duplicate_observation_with_equivalent_timezones_is_rejected():
    first = row("2024-01-02")
    second = first.replace("2024-01-02T21:00:00+00:00", "2024-01-02T13:00:00-08:00")
    text = HEADER + "\n" + first + "\n" + second + "\n"
    try:
        parse_csv(text)
    except ValueError as exc:
        assert "duplicate" in str(exc)
    else:
        raise AssertionError("equivalent UTC timestamps must be rejected")


def test_naive_timestamp_is_rejected():
    text = HEADER + "\n2024-01-02T21:00:00,2024-01-02T21:00:00,licensed-source,v1,skew-method-v1,abc123,5000,15,130\n"
    try:
        parse_csv(text)
    except ValueError as exc:
        assert "timezone is required" in str(exc)
    else:
        raise AssertionError("timezone-less timestamps must be rejected")


def test_missing_methodology_provenance_is_rejected():
    text = HEADER + "\n2024-01-02T21:00:00+00:00,2024-01-02T21:00:00+00:00,licensed-source,v1,,abc123,5000,15,130\n"
    try:
        parse_csv(text)
    except ValueError as exc:
        assert "missing required provenance" in str(exc)
    else:
        raise AssertionError("methodology version is mandatory")


def test_hash_changes_when_observation_changes():
    a = parse_csv(HEADER + "\n" + row("2024-01-02", 130))
    b = parse_csv(HEADER + "\n" + row("2024-01-02", 131))
    assert dataset_content_hash(a) != dataset_content_hash(b)
