"""ARSO weather maps."""
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
            map_type=MapType.CloudCoverage,
            rendering=MapRenderingType.Image,
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
    bbox: list[float] = []
    if map_type is not MapType.WeatherCondition:
        bbox = [44.67, 12.1, 47.42, 17.44]

    ids = await get_map_ids_for_type(map_type)
    if not ids:
        raise UnsupportedMapTypeException()

    data = await get_map_data(ids)
    data.sort(key=lambda x: x["timestamp"])

    layers: list[MapLayer] = [
        MapLayer(
            url=record["url"],
            timestamp=record["timestamp"],
            observation=ObservationType(record["observation"]),
        )
        for record in data
    ]

    return layers, bbox


def get_map_legend(map_type: MapType) -> MapLegend:  # noqa: PLR0915
    """Get ARSO map legend."""
    if map_type == MapType.Precipitation:
        items = []
        items.append(MapLegendItem(value="", color="transparent", placeholder=True))
        items.append(MapLegendItem(value="0", color="transparent"))
        items.append(MapLegendItem(value="15", color="#3e67ff"))
        items.append(MapLegendItem(value="18", color="#3797ff"))
        items.append(MapLegendItem(value="21", color="#30c1f6"))
        items.append(MapLegendItem(value="24", color="#31e7fc"))
        items.append(MapLegendItem(value="27", color="#33d397"))
        items.append(MapLegendItem(value="30", color="#2fef28"))
        items.append(MapLegendItem(value="33", color="#8bfa36"))
        items.append(MapLegendItem(value="36", color="#c8fa33"))
        items.append(MapLegendItem(value="39", color="#f6fb2a"))
        items.append(MapLegendItem(value="42", color="#fed430"))
        items.append(MapLegendItem(value="45", color="#ff9a2c"))
        items.append(MapLegendItem(value="48", color="#fe6637"))
        items.append(MapLegendItem(value="51", color="#d42e38"))
        items.append(MapLegendItem(value="54", color="#b22923"))
        items.append(MapLegendItem(value="57", color="#d436d7"))
        items.append(MapLegendItem(value="dBZ", color="transparent", placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.WindSpeed:
        items = []
        items.append(MapLegendItem(value="", color="transparent", placeholder=True))
        items.append(MapLegendItem(value="0", color="transparent"))
        items.append(MapLegendItem(value="10", color="#09609680"))
        items.append(MapLegendItem(value="20", color="#096"))
        items.append(MapLegendItem(value="30", color="#96c"))
        items.append(MapLegendItem(value="40", color="#e54cff"))
        items.append(MapLegendItem(value="50", color="#f09"))
        items.append(MapLegendItem(value="60", color="#e51919"))
        items.append(MapLegendItem(value="70", color="#933"))
        items.append(MapLegendItem(value="80", color="#4c3333"))
        items.append(MapLegendItem(value="90", color="#630"))
        items.append(MapLegendItem(value="100", color="#963"))
        items.append(MapLegendItem(value="110", color="#b29966"))
        items.append(MapLegendItem(value="km/h", color="transparent", placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.Temperature:
        items = []
        items.append(MapLegendItem(value="", color="transparent", placeholder=True))
        items.append(MapLegendItem(value="-22", color="#fff"))
        items.append(MapLegendItem(value="-20", color="#e1e1e1"))
        items.append(MapLegendItem(value="-18", color="#bebebe"))
        items.append(MapLegendItem(value="-16", color="#828282"))
        items.append(MapLegendItem(value="-14", color="#565474"))
        items.append(MapLegendItem(value="-12", color="#59447f"))
        items.append(MapLegendItem(value="-10", color="#47007f"))
        items.append(MapLegendItem(value="-8", color="#32007f"))
        items.append(MapLegendItem(value="-6", color="#0000ac"))
        items.append(MapLegendItem(value="-4", color="#0000f0"))
        items.append(MapLegendItem(value="-2", color="#2059e7"))
        items.append(MapLegendItem(value="0", color="#007eff"))
        items.append(MapLegendItem(value="2", color="#00beff"))
        items.append(MapLegendItem(value="4", color="#aff"))
        items.append(MapLegendItem(value="6", color="#01f7c6"))
        items.append(MapLegendItem(value="8", color="#18d78c"))
        items.append(MapLegendItem(value="10", color="#00aa64"))
        items.append(MapLegendItem(value="12", color="#2baa2b"))
        items.append(MapLegendItem(value="14", color="#2bc82b"))
        items.append(MapLegendItem(value="16", color="#01ff00"))
        items.append(MapLegendItem(value="18", color="#cf0"))
        items.append(MapLegendItem(value="20", color="#ff0"))
        items.append(MapLegendItem(value="22", color="#eded7e"))
        items.append(MapLegendItem(value="24", color="#e4cc66"))
        items.append(MapLegendItem(value="26", color="#dcae49"))
        items.append(MapLegendItem(value="28", color="#fa0"))
        items.append(MapLegendItem(value="30", color="#f50"))
        items.append(MapLegendItem(value="32", color="red"))
        items.append(MapLegendItem(value="34", color="#c80000"))
        items.append(MapLegendItem(value="36", color="#780000"))
        items.append(MapLegendItem(value="38", color="#640000"))
        items.append(MapLegendItem(value="40", color="#500000"))
        items.append(MapLegendItem(value="°C", color="transparent", placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.HailProbability:
        items = []
        items.append(MapLegendItem(value="", color="transparent", placeholder=True))
        items.append(MapLegendItem(value="", color="transparent"))
        items.append(MapLegendItem(value="low", color="#fae100", translatable=True))
        items.append(
            MapLegendItem(value="moderate", color="#fa7d00", translatable=True),
        )
        items.append(MapLegendItem(value="large", color="#fa0000", translatable=True))
        items.append(
            MapLegendItem(
                value="probability",
                color="transparent",
                translatable=True,
                placeholder=True,
            ),
        )
        return MapLegend(map_type=map_type, items=items)

    raise UnsupportedMapTypeException()


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
        raise UnrecognisedMapIDException()

    records = await get_weather_records(ids)

    conditions_list = []
    for record in records:
        station, condition = await parse_record(
            record,
            ObservationType.Recent if map_id == "current" else ObservationType.Forecast,
        )
        if not station:
            continue
        conditions_list.append(
            WeatherInfoExtended(station=station, condition=condition),
        )

    return conditions_list
