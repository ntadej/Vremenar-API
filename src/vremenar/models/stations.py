"""Station models."""

from pydantic import BaseModel
from typing import Optional

from .common import Coordinate


class StationInfo:
    """Station info model."""

    def __init__(
        self,
        id: str,
        title: str,
        coordinate: Coordinate,
        location_type: Optional[str] = None,
        admin_level: Optional[int] = None,
        zoom_level: Optional[float] = None,
    ) -> None:
        """Initialise station info model."""
        self.id: str = id
        self.title: str = title
        self.coordinate: Coordinate = coordinate
        self.location_type: Optional[str] = location_type
        self.admin_level: Optional[int] = admin_level
        self.zoom_level: Optional[float] = zoom_level


class StationSearchModel(BaseModel):
    """Station search body model."""

    string: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
