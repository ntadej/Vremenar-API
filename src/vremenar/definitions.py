"""Common backend definitions."""

from enum import Enum


class CountryID(str, Enum):
    """Supported countries ID enum."""

    Slovenia = "si"
    Germany = "de"

    def label(self) -> str:
        """Get country label."""
        if self is CountryID.Slovenia:
            return "Slovenia"
        if self is CountryID.Germany:
            return "Germany"
        raise RuntimeError("Undefined behaviour")  # pragma: no cover

    def full_name(self) -> str:
        """Get country full name."""
        if self is CountryID.Slovenia:
            return "slovenia"
        if self is CountryID.Germany:
            return "germany"
        raise RuntimeError("Undefined behaviour")  # pragma: no cover


class LanguageID(str, Enum):
    """Supported languages ID enum."""

    English = "en"
    German = "de"
    Slovenian = "sl"


class ObservationType(str, Enum):
    """Observation type enum."""

    Historical = "historical"
    Recent = "recent"
    Forecast = "forecast"
