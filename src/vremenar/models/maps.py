"""Map models."""

from enum import Enum
from pydantic import BaseModel, Field
from typing import List, Optional

from ..definitions import ObservationType


class MapType(str, Enum):
    """Map type enum."""

    WeatherCondition = 'condition'
    Precipitation = 'precipitation'
    CloudCoverage = 'cloud'
    WindSpeed = 'wind'
    Temperature = 'temperature'
    HailProbability = 'hail'


class MapRenderingType(str, Enum):
    """Map rendering type enum."""

    Image = 'image'
    Tiles = 'tiles'
    Icons = 'icons'


class MapLayer(BaseModel):
    """Map layer model."""

    observation: ObservationType = Field(..., example=ObservationType.Recent)
    url: str = Field(..., example='/stations/map/current?country=si')
    timestamp: str = Field(..., example='1604779200000')

    class Config:
        """Map layer model config."""

        title: str = 'Map layer'


class MapLayersList(BaseModel):
    """Map layers list model."""

    map_type: MapType = Field(..., example=MapType.Precipitation)
    rendering: MapRenderingType = Field(..., example=MapRenderingType.Image)
    layers: List[MapLayer]
    bbox: Optional[List[float]] = Field(None, example=[44.67, 12.1, 47.42, 17.44])

    @classmethod
    def init(
        cls, map_type: MapType, bbox: List[float], layers: List[MapLayer]
    ) -> 'MapLayersList':
        """Initialise map response model."""
        rendering: MapRenderingType = (
            MapRenderingType.Image if bbox else MapRenderingType.Tiles
        )
        if map_type == MapType.WeatherCondition:
            rendering = MapRenderingType.Icons

        return cls(map_type=map_type, rendering=rendering, layers=layers, bbox=bbox)

    class Config:
        """Map layers list model config."""

        title: str = 'Map layers list'
