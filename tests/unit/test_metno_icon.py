"""MET.no weather icon tests."""

from datetime import UTC, datetime

from vremenar.models.common import Coordinate
from vremenar.sources.metno.utils import get_icon, get_icon_base, get_icon_condition


def test_icon_base() -> None:
    """Test icon base."""
    assert get_icon_base({"symbol_code": "fog"}) == "FG"

    assert get_icon_base({}) == "clear"
    assert get_icon_base({"cloud_area_fraction": 0}) == "clear"
    assert get_icon_base({"cloud_area_fraction": 30}) == "partCloudy"
    assert get_icon_base({"cloud_area_fraction": 60}) == "prevCloudy"
    assert get_icon_base({"cloud_area_fraction": 90}) == "overcast"


def test_icon_condition() -> None:
    """Test icon condition."""
    available_conditions = [
        "fog",
        "sleet",
        "heavyrain",
        "snow",
        "rainandthunder",
        "",
    ]
    results_conditions = [
        "RA",
        "SHGR",
        "RA",
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
    assert not get_icon_condition({"precipitation_amount": 0})

    for condition, result in zip(available_conditions, results_conditions, strict=True):
        for intensity, result_prefix in zip(
            test_intensities,
            results_intensities,
            strict=True,
        ):
            assert (
                get_icon_condition(
                    {"symbol_code": condition, "precipitation_amount": intensity},
                )
                == f"{result_prefix}{result}"
            )


def test_icon() -> None:
    """Test icon."""
    get_icon(
        {"symbol_code": "clear_day", "precipitation_amount": 0},
        Coordinate(latitude=0.0, longitude=0.0),
        datetime.now(UTC),
    )

    get_icon(
        {"symbol_code": "sleet", "precipitation_amount": 10},
        Coordinate(latitude=0.0, longitude=0.0),
        datetime.now(UTC),
    )
