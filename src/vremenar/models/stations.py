"""Station models."""

from pydantic import BaseModel, Field
from typing import Optional

from .common import Coordinate
from .weather import WeatherCondition


class StationInfo(BaseModel):
    """Station info model."""

    id: str = Field(..., title='Identifier', example='METEO-0038')
    name: str = Field(..., example='Bled')
    coordinate: Coordinate
    zoom_level: Optional[float] = Field(None, example=7.5)

    class Config:
        """Station info model config."""

        title: str = 'Weather station information'


class ExtendedStationInfo(StationInfo):
    """Extended station info model."""

    current_condition: WeatherCondition

    @classmethod
    def from_station(
        cls, station: StationInfo, condition: WeatherCondition
    ) -> 'ExtendedStationInfo':
        """Create from station and condition."""
        return cls(
            id=station.id,
            name=station.name,
            coordinate=station.coordinate,
            zoom_level=station.zoom_level,
            current_condition=condition,
        )

    class Config:
        """Extended station info model config."""

        title: str = 'Weather station with current condition'


class StationSearchModel(BaseModel):
    """Station search body model."""

    string: Optional[str] = Field(None, example='Bled')
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)

    class Config:
        """Station search body config."""

        title: str = 'Station search body'
