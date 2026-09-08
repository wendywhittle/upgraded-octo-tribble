from app.agent_runner import CallableModelProvider


def test_provider_name_must_be_nonempty():
    try:
        CallableModelProvider(lambda p: {}, name="")
    except ValueError:
        return
    raise AssertionError("Expected ValueError")
