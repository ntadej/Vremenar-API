"""Common backend definitions."""

from enum import Enum


class CountryID(str, Enum):
    """Supported countries ID enum."""

    Slovenia = 'si'
    Germany = 'de'


class ObservationType(str, Enum):
    """Observation type enum."""

    Historical = 'historical'
    Recent = 'recent'
    Forecast = 'forecast'
