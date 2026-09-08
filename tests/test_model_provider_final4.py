from app.agent_runner import CallableModelProvider


def test_provider_name_is_preserved():
    provider = CallableModelProvider(lambda payload: {}, name="fixture")
    assert provider.name == "fixture"
