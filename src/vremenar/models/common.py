"""Common models and data structures."""

from pydantic import BaseModel, Field


class Coordinate(BaseModel):
    """Coordinate model."""

    latitude: float = Field(..., example=46.364444)
    longitude: float = Field(..., example=14.094722)
    altitude: float | None = Field(None, example=487)
