"""Station models."""

from pydantic import BaseModel, Field
from typing import Any

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
    zoom_level: float | None = Field(None, example=7.5)
    forecast_only: bool | None = Field(False, example=False)
    alerts_area: str | None = Field(None, example='SI007')

    def base(self) -> StationBase:
        """Return an instance of StationBase."""
        return self.copy(include={'id'})

    class Config:
        """Station info model config."""

        title: str = 'Weather station information'


class StationInfoExtended(StationInfo):
    """Station extended info model."""

    metadata: dict[str, Any] | None = Field(None)

    def info(self) -> StationInfo:
        """Return an instance of StationInfo."""
        return self.copy(exclude={'metadata'})

    class Config:
        """Station extended info model config."""

        title: str = 'Weather station extended information'


class StationSearchModel(BaseModel):
    """Station search body model."""

    string: str | None = Field(None, example='Bled')
    latitude: float | None = Field(None)
    longitude: float | None = Field(None)

    class Config:
        """Station search body config."""

        title: str = 'Station search body'
