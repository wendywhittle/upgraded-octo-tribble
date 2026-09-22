from growth.research import ResearchObservation, append_observation


def test_research_observation_is_append_only(tmp_path):
    path = str(tmp_path / "observations.jsonl")
    observation = ResearchObservation(
        prospect_id="ATG-VIKING-000001",
        source="human-reviewed source capture",
        observed_at="2026-09-21T00:00:00+00:00",
        facts=("industrial acquisition appetite documented",),
    )

    append_observation(path, observation)
    append_observation(path, observation)

    lines = open(path, encoding="utf-8").read().splitlines()
    assert len(lines) == 2
    assert lines[0] == lines[1]
