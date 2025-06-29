"""Weather models."""

from pydantic import BaseModel, ConfigDict

from vremenar.definitions import ObservationType
from vremenar.models.stations import StationBase, StationInfo


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


class WeatherStatistics(BaseModel):
    """Weather statistics model."""

    timestamp: str
    temperature_average_24h: float
    temperature_average_48h: float
    temperature_min_24h: float
    temperature_max_24h: float
    timestamp_temperature_min_24h: str
    timestamp_temperature_max_24h: str

    model_config = ConfigDict(
        title="Weather condition",
        json_schema_extra={
            "examples": [
                {
                    "timestamp": "1604779200000",
                    "temperature_average_24h": 17.5,
                    "temperature_average_48h": 18.5,
                    "temperature_min_24h": 10.5,
                    "temperature_max_24h": 24.3,
                    "timestamp_temperature_min_24h": "1604779200000",
                    "timestamp_temperature_max_24h": "1604779200000",
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

    def base(self) -> WeatherInfo:
        """Return an instance of WeatherInfo."""
        return WeatherInfo(station=self.station.base(), condition=self.condition)

    model_config = ConfigDict(
        title="Weather information with extended station information",
    )


class WeatherDetails(BaseModel):
    """Weather details model."""

    station: StationInfo
    condition: WeatherCondition
    statistics: WeatherStatistics

    model_config = ConfigDict(title="Weather details")
