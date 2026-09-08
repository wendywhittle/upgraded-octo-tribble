from app.agent_runner import CallableModelProvider


def test_provider_has_no_execution_surface():
    provider = CallableModelProvider(lambda payload: {}, name="fixture")
    assert not hasattr(provider, "brokerage")
    assert not hasattr(provider, "execute")
