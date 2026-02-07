"""Common backend definitions."""

from __future__ import annotations

from enum import StrEnum


class CountryID(StrEnum):
    """Supported countries ID enum."""

    Slovenia = "si"
    Germany = "de"
    Global = "global"

    def label(self) -> str:
        """Get country label."""
        if self is CountryID.Slovenia:
            return "Slovenia"
        if self is CountryID.Germany:
            return "Germany"
        if self is CountryID.Global:
            return "Global"
        raise RuntimeError  # pragma: no cover

    def full_name(self) -> str:
        """Get country full name."""
        if self is CountryID.Slovenia:
            return "slovenia"
        if self is CountryID.Germany:
            return "germany"
        if self is CountryID.Global:
            return "global"
        raise RuntimeError  # pragma: no cover


class LanguageID(StrEnum):
    """Supported languages ID enum."""

    English = "en"
    German = "de"
    Slovenian = "sl"


class ObservationType(StrEnum):
    """Observation type enum."""

    Historical = "historical"
    Recent = "recent"
    Forecast = "forecast"
