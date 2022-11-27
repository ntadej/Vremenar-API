"""Weather models."""

from pydantic import BaseModel, Field

from .stations import StationBase, StationInfo
from ..definitions import ObservationType


class WeatherCondition(BaseModel):
    """Weather condition model."""

    observation: ObservationType = Field(..., example=ObservationType.Recent)
    timestamp: str = Field(..., example="1604779200000")
    icon: str = Field(..., example="clear_night")
    temperature: float = Field(..., example=13)
    temperature_low: float | None = Field(None, example=1)

    class Config:
        """Weather condition model config."""

        title: str = "Weather condition"


class WeatherInfo(BaseModel):
    """Weather info model."""

    station: StationBase
    condition: WeatherCondition

    class Config:
        """Weather info model config."""

        title: str = "Weather information"


class WeatherInfoExtended(WeatherInfo):
    """Weather extended info model."""

    station: StationInfo

    def base(self) -> WeatherInfo:
        """Return an instance of WeatherInfo."""
        return WeatherInfo(station=self.station.base(), condition=self.condition)

    class Config:
        """Weather extended info model config."""

        title: str = "Weather information with extended station information"
