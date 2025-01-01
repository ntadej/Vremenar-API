"""Map models."""

from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict

from vremenar.definitions import ObservationType

from . import get_examples


class MapType(str, Enum):
    """Map type enum."""

    WeatherCondition = "condition"
    Precipitation = "precipitation"
    PrecipitationGlobal = "precipitation_global"
    CloudCoverage = "cloud"
    CloudCoverageInfraredGlobal = "cloud_infrared_global"
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

    map_type: MapType
    rendering: MapRenderingType
    has_legend: bool | None = None

    model_config = ConfigDict(
        title="Supported map type",
        json_schema_extra={
            "examples": [
                {
                    "map_type": MapType.Precipitation,
                    "rendering": MapRenderingType.Tiles,
                    "has_legend": False,
                },
            ],
        },
    )


class MapLayer(BaseModel):
    """Map layer model."""

    observation: ObservationType
    url: str
    timestamp: str

    model_config = ConfigDict(
        title="Map layer",
        json_schema_extra={
            "examples": [
                {
                    "observation": ObservationType.Recent,
                    "url": "/stations/map/current?country=si",
                    "timestamp": "1604779200000",
                },
            ],
        },
    )


class MapLayersList(BaseModel):
    """Map layers list model."""

    map_type: MapType
    rendering: MapRenderingType
    layers: list[MapLayer]
    bbox: list[float] | None = None

    @classmethod
    def init(
        cls,
        map_type: MapType,
        bbox: list[float],
        layers: list[MapLayer],
    ) -> MapLayersList:
        """Initialise map response model."""
        rendering: MapRenderingType = (
            MapRenderingType.Image if bbox else MapRenderingType.Tiles
        )
        if map_type == MapType.WeatherCondition:
            rendering = MapRenderingType.Icons

        return cls(map_type=map_type, rendering=rendering, layers=layers, bbox=bbox)

    model_config = ConfigDict(
        title="Map layers list",
        json_schema_extra={
            "examples": [
                {
                    "map_type": MapType.Precipitation,
                    "rendering": MapRenderingType.Image,
                    "layers": get_examples(MapLayer.model_config),
                    "bbox": [44.67, 12.1, 47.42, 17.44],
                },
            ],
        },
    )


class MapLegendItem(BaseModel):
    """Map legend item model."""

    value: str
    color: str
    placeholder: bool | None = None
    translatable: bool | None = None

    model_config = ConfigDict(
        title="Map legend item",
        json_schema_extra={
            "examples": [
                {
                    "value": "30",
                    "color": "#2fef28",
                    "placeholder": False,
                    "translatable": False,
                },
            ],
        },
    )


class MapLegend(BaseModel):
    """Map legend model."""

    map_type: MapType
    items: list[MapLegendItem]

    model_config = ConfigDict(
        title="Map legend",
        json_schema_extra={
            "examples": [
                {
                    "map_type": MapType.Precipitation,
                    "items": get_examples(MapLegendItem.model_config),
                },
            ],
        },
    )
