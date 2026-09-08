from app.agent_runner import CallableModelProvider


def test_provider_identity():
    assert CallableModelProvider(lambda p: {}, name="fixture").name == "fixture"
