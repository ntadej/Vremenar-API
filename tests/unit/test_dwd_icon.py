"""DWD weather icon tests."""

from vremenar.sources.dwd.utils import get_icon_base, get_icon_condition


def test_icon_base() -> None:
    """Test icon base."""
    assert get_icon_base({"condition": "fog"}) == "FG"

    assert get_icon_base({}) == "clear"
    assert get_icon_base({"cloud_cover": 0}) == "clear"
    assert get_icon_base({"cloud_cover": 30}) == "partCloudy"
    assert get_icon_base({"cloud_cover": 60}) == "prevCloudy"
    assert get_icon_base({"cloud_cover": 90}) == "overcast"


def test_icon_condition() -> None:
    """Test icon condition."""
    available_conditions = [
        "dry",
        "fog",
        "hail",
        "rain",
        "sleet",
        "snow",
        "thunderstorm",
        None,
    ]
    results_conditions = [
        None,
        "RA",
        "SHGR",
        "RA",
        "SHGR",
        "SN",
        "TSRA",
        "RA",
    ]

    test_intensities = [
        0.5,
        5.0,
        15.0,
    ]
    results_intensities = [
        "light",
        "mod",
        "heavy",
    ]

    assert not get_icon_condition({})
    assert not get_icon_condition({"precipitation": 0})
    assert not get_icon_condition({"precipitation_60": 0})

    for condition, result in zip(available_conditions, results_conditions, strict=True):
        for intensity, result_prefix in zip(
            test_intensities,
            results_intensities,
            strict=True,
        ):
            if result is None:
                assert not get_icon_condition(
                    {"condition": condition, "precipitation": intensity},
                )
            else:
                assert (
                    get_icon_condition(
                        {"condition": condition, "precipitation": intensity},
                    )
                    == f"{result_prefix}{result}"
                )
