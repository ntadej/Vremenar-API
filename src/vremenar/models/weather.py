"""Weather models."""
from __future__ import annotations

from pydantic import BaseModel, ConfigDict

from vremenar.definitions import ObservationType
from vremenar.models.stations import StationBase, StationInfo  # noqa: TCH001


class WeatherCondition(BaseModel):
    """Weather condition model."""

    observation: ObservationType
    timestamp: str
    icon: str
    temperature: float
    temperature_low: float | None = None

    model_config = ConfigDict(
        title="Weather condition",
        json_schema_extra={
            "examples": [
                {
                    "observation": ObservationType.Recent,
                    "timestamp": "1604779200000",
                    "icon": "clear_night",
                    "temperature": 13,
                    "temperature_low": 1,
                },
            ],
        },
    )


class WeatherInfo(BaseModel):
    """Weather info model."""

    station: StationBase
    condition: WeatherCondition

    model_config = ConfigDict(title="Weather information")


class WeatherInfoExtended(WeatherInfo):
    """Weather extended info model."""

    station: StationInfo

    def base(self: WeatherInfoExtended) -> WeatherInfo:
        """Return an instance of WeatherInfo."""
        return WeatherInfo(station=self.station.base(), condition=self.condition)

    model_config = ConfigDict(
        title="Weather information with extended station information",
    )
