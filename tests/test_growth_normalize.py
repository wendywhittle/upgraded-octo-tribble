from growth.normalize import normalize_observation


def test_normalize_observation_strips_and_drops_blank_facts():
    observation = normalize_observation(
        "ATG-000001",
        "public-source",
        "2026-09-21",
        ["  actively seeking investments  ", "", " industrial "],
    )

    assert observation.prospect_id == "ATG-000001"
    assert observation.source == "public-source"
    assert observation.facts == (
        "actively seeking investments",
        "industrial",
    )
