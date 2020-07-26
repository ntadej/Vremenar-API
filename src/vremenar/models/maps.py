"""Map models."""

from enum import Enum
from typing import List, Optional

from ..definitions import ObservationType


class MapType(str, Enum):
    """Map type enum."""

    # Forecast = 'forecast'
    Precipitation = 'precipitation'
    CloudCoverage = 'cloud'
    WindSpeed = 'wind'
    Temperature = 'temperature'
    HailProbability = 'hail'


class MapRenderingType(str, Enum):
    """Map rendering type enum."""

    Image = 'image'
    Tiles = 'tiles'


class MapLayer:
    """Map layer model."""

    def __init__(self, url: str, time: str, observation: ObservationType) -> None:
        """Initialise map layer model."""
        self.observation: ObservationType = observation
        self.url: str = url
        self.timestamp: str = time


class MapResponse:
    """Map response model."""

    def __init__(
        self, map_type: MapType, bbox: List[float], layers: List[MapLayer]
    ) -> None:
        """Initialise map response model."""
        self.map_type: MapType = map_type
        self.rendering = MapRenderingType.Image if bbox else MapRenderingType.Tiles
        self.layers: List[MapLayer] = layers
        self.bbox: Optional[List[float]] = bbox
