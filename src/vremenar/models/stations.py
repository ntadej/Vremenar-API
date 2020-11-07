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


class StationSearchModel(BaseModel):
    """Station search body model."""

    string: Optional[str] = Field(None, example='Bled')
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)

    class Config:
        """Station search body config."""

        title: str = 'Station search body'
