"""Common backend definitions."""

from enum import Enum


class CountryID(str, Enum):
    """Supported countries ID enum."""

    Slovenia = 'si'
    Germany = 'de'

    def full_name(self) -> str:
        """Get country full name."""
        if self is CountryID.Slovenia:
            return 'slovenia'
        if self is CountryID.Germany:
            return 'germany'


class LanguageID(str, Enum):
    """Supported languages ID enum."""

    English = 'en'
    German = 'de'
    Slovenian = 'sl'


class ObservationType(str, Enum):
    """Observation type enum."""

    Historical = 'historical'
    Recent = 'recent'
    Forecast = 'forecast'
