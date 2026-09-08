import pytest

from app.agent_registry import build_default_registry
from app.model_backend import CallableModelBackend, ModelBackendError


def test_backend_contains_failures():
    agent = build_default_registry().get("researcher")

    def invoke(context):
        raise RuntimeError("backend unavailable")

    with pytest.raises(ModelBackendError, match="model backend failed"):
        CallableModelBackend(invoke).assess(agent, "q", [])
