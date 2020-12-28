"""Units tests."""

from ..units import celsius_to_kelvin, kelvin_to_celsius


def test_temperature() -> None:
    """Test temperature conversions."""
    assert celsius_to_kelvin(23.5) == 296.65
    assert kelvin_to_celsius(296.324) == 23.17
