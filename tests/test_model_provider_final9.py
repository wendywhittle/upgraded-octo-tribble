from app.agent_runner import CallableModelProvider


def test_callable_provider_accepts_callable():
    provider = CallableModelProvider(lambda payload: {}, name="fixture")
    assert callable(provider.model_callable)
