from app.agent_registry import build_default_registry


def test_default_registry_has_expected_perspectives():
    assert build_default_registry().ids() == [
        "researcher", "quant", "investor", "scientist", "systems",
        "contrarian", "philosopher", "observer", "meta_intelligence", "governance",
    ]
