from app.agent_runner import CallableModelProvider


def test_callable_provider_receives_mapping():
    seen = []
    provider = CallableModelProvider(lambda payload: seen.append(payload) or {}, name="fixture")
    provider.model_callable({"question": "Q"})
    assert seen == [{"question": "Q"}]
