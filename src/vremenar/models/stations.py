"""Station models."""
from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict

from vremenar.models.common import Coordinate

from . import extend_examples, get_examples


class StationBase(BaseModel):
    """Station base model."""

    id: str

    model_config = ConfigDict(
        title="Weather station base",
        json_schema_extra={
            "examples": [
                {"id": "METEO-0038"},
            ],
        },
    )


class StationInfo(StationBase):
    """Station info model."""

    name: str
    coordinate: Coordinate
    zoom_level: float | None = None
    forecast_only: bool | None = False
    alerts_area: str | None = None

    def base(self) -> StationBase:
        """Return an instance of StationBase."""
        data = self.model_dump(include={"id"})
        return StationBase.model_validate(data)

    model_config = ConfigDict(
        title="Weather station information",
        json_schema_extra={
            "examples": extend_examples(
                StationBase.model_config,
                {
                    "name": "Bled",
                    "coordinate": get_examples(Coordinate.model_config)[0],
                    "zoom_level": 7.5,
                    "forecast_only": False,
                    "alerts_area": "SI007",
                },
            ),
        },
    )


class StationInfoExtended(StationInfo):
    """Station extended info model."""

    metadata: dict[str, Any] | None = None

    def info(self) -> StationInfo:
        """Return an instance of StationInfo."""
        data = self.model_dump(exclude={"metadata"})
        return StationInfo.model_validate(data)

    model_config = ConfigDict(title="Weather station extended information")


class StationSearchModel(BaseModel):
    """Station search body model."""

    latitude: float | None = None
    longitude: float | None = None

    model_config = ConfigDict(
        title="Station search body",
        json_schema_extra={
            "examples": [
                {
                    "latitude": 46.364444,
                    "longitude": 14.094722,
                },
            ],
        },
    )
