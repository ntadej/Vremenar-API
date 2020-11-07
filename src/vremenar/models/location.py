"""Location models."""

from pydantic import BaseModel
from typing import Optional


class LocationSearchModel(BaseModel):
    """Location search body model."""

    string: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
