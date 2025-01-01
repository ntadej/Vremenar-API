"""Common models and data structures."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class Coordinate(BaseModel):
    """Coordinate model."""

    latitude: float
    longitude: float
    altitude: float | None = None

    model_config = ConfigDict(
        title="Coordinate",
        json_schema_extra={
            "examples": [
                {
                    "latitude": 46.364444,
                    "longitude": 14.094722,
                    "altitude": 487,
                },
            ],
        },
    )
