"""ARSO weather maps."""

from __future__ import annotations

import operator

from vremenar.definitions import ObservationType
from vremenar.exceptions import UnrecognisedMapIDException, UnsupportedMapTypeException
from vremenar.models.maps import (
    MapLayer,
    MapLegend,
    MapLegendItem,
    MapRenderingType,
    MapType,
    SupportedMapType,
)
from vremenar.models.weather import WeatherInfoExtended
from vremenar.sources.librewxr import (
    get_global_map_cloud_infrared,
    get_global_map_precipitation,
    get_librewxr_map_legend,
)
from vremenar.utils import logger

from .utils import (
    get_map_data,
    get_map_ids_for_type,
    get_weather_ids_for_timestamp,
    get_weather_records,
    parse_record,
)


def get_supported_map_types() -> list[SupportedMapType]:
    """Get ARSO supported map types."""
    return [
        SupportedMapType(
            map_type=MapType.WeatherCondition,
            rendering=MapRenderingType.Icons,
        ),
        SupportedMapType(
            map_type=MapType.Precipitation,
            rendering=MapRenderingType.Image,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.PrecipitationGlobal,
            rendering=MapRenderingType.Tiles,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.CloudCoverage,
            rendering=MapRenderingType.Image,
        ),
        SupportedMapType(
            map_type=MapType.CloudCoverageInfraredGlobal,
            rendering=MapRenderingType.Tiles,
        ),
        SupportedMapType(
            map_type=MapType.WindSpeed,
            rendering=MapRenderingType.Image,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.Temperature,
            rendering=MapRenderingType.Image,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.HailProbability,
            rendering=MapRenderingType.Image,
            has_legend=True,
        ),
    ]


async def get_map_layers(map_type: MapType) -> tuple[list[MapLayer], list[float]]:
    """Get ARSO map layers."""
    if map_type == MapType.PrecipitationGlobal:
        return await get_global_map_precipitation()

    if map_type == MapType.CloudCoverageInfraredGlobal:
        return await get_global_map_cloud_infrared()

    bbox: list[float] = []
    if map_type is not MapType.WeatherCondition:
        bbox = [44.67, 12.1, 47.42, 17.44]

    ids = await get_map_ids_for_type(map_type)
    if not ids:
        raise UnsupportedMapTypeException

    data = await get_map_data(ids)
    data.sort(key=operator.itemgetter("timestamp"))

    layers: list[MapLayer] = [
        MapLayer(
            url=record["url"],
            timestamp=record["timestamp"],
            observation=ObservationType(record["observation"]),
        )
        for record in data
    ]

    return layers, bbox


def get_map_legend(map_type: MapType) -> MapLegend:
    """Get ARSO map legend."""
    if map_type == MapType.PrecipitationGlobal:
        return get_librewxr_map_legend(map_type)

    if map_type == MapType.Precipitation:
        items = [
            MapLegendItem(value="", color="transparent", placeholder=True),
            MapLegendItem(value="0", color="transparent"),
            MapLegendItem(value="15", color="#3e67ff"),
            MapLegendItem(value="18", color="#3797ff"),
            MapLegendItem(value="21", color="#30c1f6"),
            MapLegendItem(value="24", color="#31e7fc"),
            MapLegendItem(value="27", color="#33d397"),
            MapLegendItem(value="30", color="#2fef28"),
            MapLegendItem(value="33", color="#8bfa36"),
            MapLegendItem(value="36", color="#c8fa33"),
            MapLegendItem(value="39", color="#f6fb2a"),
            MapLegendItem(value="42", color="#fed430"),
            MapLegendItem(value="45", color="#ff9a2c"),
            MapLegendItem(value="48", color="#fe6637"),
            MapLegendItem(value="51", color="#d42e38"),
            MapLegendItem(value="54", color="#b22923"),
            MapLegendItem(value="57", color="#d436d7"),
            MapLegendItem(value="dBZ", color="transparent", placeholder=True),
        ]
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.WindSpeed:
        items = [
            MapLegendItem(value="", color="transparent", placeholder=True),
            MapLegendItem(value="0", color="transparent"),
            MapLegendItem(value="10", color="#09609680"),
            MapLegendItem(value="20", color="#096"),
            MapLegendItem(value="30", color="#96c"),
            MapLegendItem(value="40", color="#e54cff"),
            MapLegendItem(value="50", color="#f09"),
            MapLegendItem(value="60", color="#e51919"),
            MapLegendItem(value="70", color="#933"),
            MapLegendItem(value="80", color="#4c3333"),
            MapLegendItem(value="90", color="#630"),
            MapLegendItem(value="100", color="#963"),
            MapLegendItem(value="110", color="#b29966"),
            MapLegendItem(value="km/h", color="transparent", placeholder=True),
        ]
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.Temperature:
        items = [
            MapLegendItem(value="", color="transparent", placeholder=True),
            MapLegendItem(value="-22", color="#fff"),
            MapLegendItem(value="-20", color="#e1e1e1"),
            MapLegendItem(value="-18", color="#bebebe"),
            MapLegendItem(value="-16", color="#828282"),
            MapLegendItem(value="-14", color="#565474"),
            MapLegendItem(value="-12", color="#59447f"),
            MapLegendItem(value="-10", color="#47007f"),
            MapLegendItem(value="-8", color="#32007f"),
            MapLegendItem(value="-6", color="#0000ac"),
            MapLegendItem(value="-4", color="#0000f0"),
            MapLegendItem(value="-2", color="#2059e7"),
            MapLegendItem(value="0", color="#007eff"),
            MapLegendItem(value="2", color="#00beff"),
            MapLegendItem(value="4", color="#aff"),
            MapLegendItem(value="6", color="#01f7c6"),
            MapLegendItem(value="8", color="#18d78c"),
            MapLegendItem(value="10", color="#00aa64"),
            MapLegendItem(value="12", color="#2baa2b"),
            MapLegendItem(value="14", color="#2bc82b"),
            MapLegendItem(value="16", color="#01ff00"),
            MapLegendItem(value="18", color="#cf0"),
            MapLegendItem(value="20", color="#ff0"),
            MapLegendItem(value="22", color="#eded7e"),
            MapLegendItem(value="24", color="#e4cc66"),
            MapLegendItem(value="26", color="#dcae49"),
            MapLegendItem(value="28", color="#fa0"),
            MapLegendItem(value="30", color="#f50"),
            MapLegendItem(value="32", color="red"),
            MapLegendItem(value="34", color="#c80000"),
            MapLegendItem(value="36", color="#780000"),
            MapLegendItem(value="38", color="#640000"),
            MapLegendItem(value="40", color="#500000"),
            MapLegendItem(value="°C", color="transparent", placeholder=True),
        ]
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.HailProbability:
        items = [
            MapLegendItem(value="", color="transparent", placeholder=True),
            MapLegendItem(value="", color="transparent"),
            MapLegendItem(value="low", color="#fae100", translatable=True),
            MapLegendItem(value="moderate", color="#fa7d00", translatable=True),
            MapLegendItem(value="large", color="#fa0000", translatable=True),
            MapLegendItem(
                value="probability",
                color="transparent",
                translatable=True,
                placeholder=True,
            ),
        ]
        return MapLegend(map_type=map_type, items=items)

    raise UnsupportedMapTypeException


def get_all_map_legends() -> list[MapLegend]:
    """Get all ARSO map legends."""
    supported = get_supported_map_types()
    return [get_map_legend(t.map_type) for t in supported if t.has_legend]


async def get_weather_map(map_id: str) -> list[WeatherInfoExtended]:
    """Get weather map from ID."""
    timestamp = map_id

    logger.debug("ARSO weather timestamp: %s", timestamp)

    ids: set[str] = await get_weather_ids_for_timestamp(timestamp)
    if not ids:
        raise UnrecognisedMapIDException

    records = await get_weather_records(ids)

    conditions_list = []
    for record in records:
        station, condition = await parse_record(
            record,
            ObservationType.Recent if map_id == "current" else ObservationType.Forecast,
        )
        if not station or not condition:  # pragma: no cover
            continue
        conditions_list.append(
            WeatherInfoExtended(station=station, condition=condition),  # ty: ignore[invalid-argument-type]
        )

    return conditions_list
