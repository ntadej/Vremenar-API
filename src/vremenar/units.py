"""Units support."""


def celsius_to_kelvin(temperature: float) -> float:
    """Convert from Celsius to Kelvin."""
    return round(temperature + 273.15, 2)


def kelvin_to_celsius(temperature: float) -> float:
    """Convert from Kelvin to Celsius ."""
    return round(temperature - 273.15, 2)
