from growth.qualification import (
    SignalCategory,
    evaluate_qualification,
)


def test_qualification_requires_acquisition_appetite_and_fit():
    result = evaluate_qualification(
        {
            SignalCategory.ACQUISITION_APPETITE,
            SignalCategory.ASSET_FIT,
        }
    )

    assert result.qualified is True
    assert result.matched == (SignalCategory.ASSET_FIT,)


def test_fit_without_acquisition_appetite_is_not_qualified():
    result = evaluate_qualification({SignalCategory.ASSET_FIT})

    assert result.qualified is False


def test_recent_activity_alone_is_not_qualification():
    result = evaluate_qualification({SignalCategory.RECENT_ACTIVITY})

    assert result.qualified is False
