"""Map models."""

from enum import Enum

from pydantic import BaseModel, Field

from vremenar.definitions import ObservationType


class MapType(str, Enum):
    """Map type enum."""

    WeatherCondition = "condition"
    Precipitation = "precipitation"
    CloudCoverage = "cloud"
    WindSpeed = "wind"
    Temperature = "temperature"
    HailProbability = "hail"
    UVIndexMax = "uv_index_max"
    UVDose = "uv_dose"


class MapRenderingType(str, Enum):
    """Map rendering type enum."""

    Image = "image"
    Tiles = "tiles"
    Icons = "icons"


class SupportedMapType(BaseModel):
    """Supported map type model."""

    map_type: MapType = Field(..., example=MapType.Precipitation)
    rendering_type: MapRenderingType = Field(..., example=MapRenderingType.Tiles)
    has_legend: bool | None = Field(None, example=False)


class MapLayer(BaseModel):
    """Map layer model."""

    observation: ObservationType = Field(..., example=ObservationType.Recent)
    url: str = Field(..., example="/stations/map/current?country=si")
    timestamp: str = Field(..., example="1604779200000")

    class Config:
        """Map layer model config."""

        title: str = "Map layer"


class MapLayersList(BaseModel):
    """Map layers list model."""

    map_type: MapType = Field(..., example=MapType.Precipitation)
    rendering: MapRenderingType = Field(..., example=MapRenderingType.Image)
    layers: list[MapLayer]
    bbox: list[float] | None = Field(None, example=[44.67, 12.1, 47.42, 17.44])

    @classmethod
    def init(
        cls,
        map_type: MapType,
        bbox: list[float],
        layers: list[MapLayer],
    ) -> "MapLayersList":
        """Initialise map response model."""
        rendering: MapRenderingType = (
            MapRenderingType.Image if bbox else MapRenderingType.Tiles
        )
        if map_type == MapType.WeatherCondition:
            rendering = MapRenderingType.Icons

        return cls(map_type=map_type, rendering=rendering, layers=layers, bbox=bbox)

    class Config:
        """Map layers list model config."""

        title: str = "Map layers list"


class MapLegendItem(BaseModel):
    """Map legend item model."""

    value: str = Field(..., example="30")
    color: str = Field(..., example="#2fef28")
    placeholder: bool | None = Field(None, example=False)
    translatable: bool | None = Field(None, example=False)

    class Config:
        """Map legend item model config."""

        title: str = "Map legend item"


class MapLegend(BaseModel):
    """Map legend model."""

    map_type: MapType = Field(..., example=MapType.Precipitation)
    items: list[MapLegendItem]

    class Config:
        """Map legend model config."""

        title: str = "Map legend"
