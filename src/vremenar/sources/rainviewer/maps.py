"""RainViewer weather maps."""

from __future__ import annotations

from typing import Any

from httpx import AsyncClient

from vremenar.definitions import ObservationType
from vremenar.exceptions import UnsupportedMapTypeException
from vremenar.models.maps import (
    MapLayer,
    MapLegend,
    MapLegendItem,
    MapRenderingType,
    MapType,
    SupportedMapType,
)

API_BASEURL = "https://api.rainviewer.com/public"


def get_supported_map_types() -> list[SupportedMapType]:
    """Get RainViewer supported map types."""
    return [
        SupportedMapType(
            map_type=MapType.PrecipitationGlobal,
            rendering=MapRenderingType.Tiles,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.CloudCoverageInfraredGlobal,
            rendering=MapRenderingType.Tiles,
        ),
    ]


async def get_global_map_precipitation() -> tuple[list[MapLayer], list[float]]:
    """Get RainViewer precipitation map layers."""
    layers: list[MapLayer] = []

    suffix: str = "/512/{z}/{x}/{y}/2/1_0.png"

    api_url = f"{API_BASEURL}/weather-maps.json"
    async with AsyncClient() as client:
        response = await client.get(api_url)
        data: dict[str, Any] = response.json()

    host: str = data["host"]
    radar: dict[str, Any] = data["radar"]

    layers += [
        MapLayer(
            url=f"{host}{item['path']}{suffix}",
            timestamp=f"{item['time']}000",
            observation=ObservationType.Historical,
        )
        for item in radar["past"]
    ]
    layers[-1].observation = ObservationType.Recent

    layers += [
        MapLayer(
            url=f"{host}{item['path']}{suffix}",
            timestamp=f"{item['time']}000",
            observation=ObservationType.Forecast,
        )
        for item in radar["nowcast"]
    ]

    return layers, []


async def get_global_map_cloud_infrared() -> tuple[list[MapLayer], list[float]]:
    """Get RainViewer cloud infrared satellite map layers."""
    layers: list[MapLayer] = []

    suffix: str = "/512/{z}/{x}/{y}/0/1_0.png"

    api_url = f"{API_BASEURL}/weather-maps.json"
    async with AsyncClient() as client:
        response = await client.get(api_url)
        data: dict[str, Any] = response.json()

    host: str = data["host"]
    satellite: dict[str, Any] = data["satellite"]

    layers += [
        MapLayer(
            url=f"{host}{item['path']}{suffix}",
            timestamp=f"{item['time']}000",
            observation=ObservationType.Historical,
        )
        for item in satellite["infrared"]
    ]
    layers[-1].observation = ObservationType.Recent

    return layers, []


async def get_map_layers(map_type: MapType) -> tuple[list[MapLayer], list[float]]:
    """Get RainViewer map layers."""
    if map_type == MapType.PrecipitationGlobal:
        return await get_global_map_precipitation()

    if map_type == MapType.CloudCoverageInfraredGlobal:
        return await get_global_map_cloud_infrared()

    raise UnsupportedMapTypeException()


def get_map_legend(map_type: MapType) -> MapLegend:
    """Get RainView map legend."""
    if map_type == MapType.PrecipitationGlobal:
        items = []
        items.append(MapLegendItem(value="", color="transparent", placeholder=True))
        items.append(MapLegendItem(value="-10", color="#636159"))
        items.append(MapLegendItem(value="-5", color="#797460"))
        items.append(MapLegendItem(value="0", color="#928871"))
        items.append(MapLegendItem(value="5", color="#CEC087"))
        items.append(MapLegendItem(value="10", color="#88DDEE"))
        items.append(MapLegendItem(value="15", color="#0099CC"))
        items.append(MapLegendItem(value="20", color="#0077AA"))
        items.append(MapLegendItem(value="25", color="#005588"))
        items.append(MapLegendItem(value="30", color="#FFEE00"))
        items.append(MapLegendItem(value="35", color="#FFAA00"))
        items.append(MapLegendItem(value="40", color="#FF7700"))
        items.append(MapLegendItem(value="45", color="#FF4400"))
        items.append(MapLegendItem(value="50", color="#EE0000"))
        items.append(MapLegendItem(value="55", color="#990000"))
        items.append(MapLegendItem(value="60", color="#FFAAFF"))
        items.append(MapLegendItem(value="65", color="#FF77FF"))
        items.append(MapLegendItem(value="70", color="#FF44FF"))
        items.append(MapLegendItem(value="75", color="#FF00FF"))
        items.append(MapLegendItem(value="80", color="#AA00AA"))
        items.append(MapLegendItem(value="dBZ", color="transparent", placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    raise UnsupportedMapTypeException()  # pragma: no cover


def get_all_map_legends() -> list[MapLegend]:
    """Get all RainViewer map legends."""
    supported = get_supported_map_types()
    return [get_map_legend(t.map_type) for t in supported if t.has_legend]
