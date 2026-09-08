import pytest

from app.agent_runner import CallableModelProvider


def test_callable_provider_requires_callable():
    with pytest.raises(TypeError):
        CallableModelProvider(None)


def test_callable_provider_requires_name():
    with pytest.raises(ValueError):
        CallableModelProvider(lambda payload: {}, name=" ")
