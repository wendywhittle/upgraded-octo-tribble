from growth.qualification import SignalCategory
from growth.research import ResearchObservation
from growth.research_adapter import (
    ResearchSignal,
    adapt_observation,
    signal_categories,
)


def test_adapter_preserves_typed_signals():
    observation = ResearchObservation(
        prospect_id="ATG-000001",
        source="https://example.com",
        observed_at="2026-09-21",
        facts=("Actively seeking acquisitions", "Industrial"),
    )
    signals = (
        ResearchSignal(
            SignalCategory.ACQUISITION_APPETITE,
            "Actively seeking acquisitions",
        ),
        ResearchSignal(SignalCategory.ASSET_FIT, "Industrial"),
    )

    adapted = adapt_observation(observation, signals)

    assert adapted == signals
    assert signal_categories(adapted) == {
        SignalCategory.ACQUISITION_APPETITE,
        SignalCategory.ASSET_FIT,
    }


def test_adapter_rejects_blank_signal_fact():
    observation = ResearchObservation(
        prospect_id="ATG-000001",
        source="https://example.com",
        observed_at="2026-09-21",
        facts=("Industrial",),
    )
    signals = (
        ResearchSignal(SignalCategory.ASSET_FIT, " "),
    )

    try:
        adapt_observation(observation, signals)
    except ValueError as exc:
        assert "signal fact" in str(exc)
    else:
        raise AssertionError("blank signal fact should be rejected")
