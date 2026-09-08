import pytest
from app.agent_runner import CallableModelProvider


def test_provider_rejects_invalid_callable():
    with pytest.raises(TypeError):
        CallableModelProvider(object())
