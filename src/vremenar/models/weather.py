"""Weather models."""

from pydantic import BaseModel, Field
from typing import Optional

from ..definitions import ObservationType
from .common import Coordinate


class WeatherCondition(BaseModel):
    """Weather condition model."""

    observation: ObservationType = Field(..., example=ObservationType.Recent)
    timestamp: str = Field(..., example='1604779200000')
    icon: str = Field(..., example='clear_night')
    temperature: float = Field(..., example=13)
    temperature_low: Optional[float] = Field(None, example=1)


class WeatherInfo:
    """Weather info model."""

    def __init__(
        self,
        id: str,
        observation: ObservationType,
        time: str,
        title: str,
        icon: str,
        temperature: float,
        coordinate: Coordinate,
        zoom_level: Optional[float] = None,
    ) -> None:
        """Initialise weather info model."""
        self.id: str = id
        self.observation: ObservationType = observation
        self.timestamp: str = time
        self.title: str = title
        self.icon: str = icon
        self.temperature: float = temperature
        self.temperature_low: Optional[float] = None
        self.coordinate: Coordinate = coordinate
        self.zoom_level: Optional[float] = zoom_level
