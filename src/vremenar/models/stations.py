"""Station models."""

from pydantic import BaseModel, Field
from typing import Any, Optional

from .common import Coordinate


class StationBase(BaseModel):
    """Station base model."""

    id: str = Field(..., title='Identifier', example='METEO-0038')

    class Config:
        """Station base model config."""

        title: str = 'Weather station base'


class StationInfo(StationBase):
    """Station info model."""

    name: str = Field(..., example='Bled')
    coordinate: Coordinate
    zoom_level: Optional[float] = Field(None, example=7.5)
    forecast_only: Optional[bool] = Field(False, example=False)

    def base(self) -> StationBase:
        """Return an instance of StationBase."""
        return self.copy(include={'id'})

    class Config:
        """Station info model config."""

        title: str = 'Weather station information'


class StationInfoExtended(StationInfo):
    """Station extended info model."""

    metadata: Optional[dict[str, Any]] = Field(None)

    def info(self) -> StationInfo:
        """Return an instance of StationInfo."""
        return self.copy(exclude={'metadata'})

    class Config:
        """Station extended info model config."""

        title: str = 'Weather station extended information'


class StationSearchModel(BaseModel):
    """Station search body model."""

    string: Optional[str] = Field(None, example='Bled')
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)

    class Config:
        """Station search body config."""

        title: str = 'Station search body'
