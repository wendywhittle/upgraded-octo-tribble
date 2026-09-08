from app.agent_registry import build_default_registry
from app.model_backend import CallableModelBackend


def test_backend_defaults_model_name_when_blank():
    agent = build_default_registry().get("quant")
    result = CallableModelBackend(
        lambda context: {"direction": "NO_DATA", "confidence": 0.0, "thesis": "none"},
        model_name="   ",
    ).assess(agent, "q", [])
    assert result["model_version"] == "unspecified"
