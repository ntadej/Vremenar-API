"""DWD weather maps."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta

from httpx2 import AsyncClient

from vremenar.definitions import CountryID, ObservationType
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
from vremenar.utils import logger, to_timestamp

from .utils import get_mosmix_ids_for_timestamp, get_weather_records, parse_record

MAPS_BASEURL = (
    "https://maps.dwd.de/geoserver/dwd/ows"
    "?service=WMS&version=1.3&request=GetMap&srs=EPSG:3857&format=image%2Fpng&transparent=true"
)
MAPS_TIMEOUT = 3

MESSAGE_MAP_URL = "DWD Map URL: %s"
MESSAGE_NOT_AVAILABLE_YET = "Map not available yet"

PRECIPITATION_BUFFER_SECONDS = 100


def get_supported_map_types() -> list[SupportedMapType]:
    """Get DWD supported map types."""
    return [
        SupportedMapType(
            map_type=MapType.WeatherCondition,
            rendering=MapRenderingType.Icons,
        ),
        SupportedMapType(
            map_type=MapType.Precipitation,
            rendering=MapRenderingType.Tiles,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.PrecipitationGlobal,
            rendering=MapRenderingType.Tiles,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.CloudCoverageInfraredGlobal,
            rendering=MapRenderingType.Tiles,
        ),
        SupportedMapType(
            map_type=MapType.Temperature,
            rendering=MapRenderingType.Tiles,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.UVIndexMax,
            rendering=MapRenderingType.Tiles,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.UVDose,
            rendering=MapRenderingType.Tiles,
            has_legend=True,
        ),
    ]


def get_map_condition() -> tuple[list[MapLayer], list[float]]:
    """Get DWD condition map layers."""
    layers: list[MapLayer] = []

    now = datetime.now(tz=UTC)
    now = now.replace(minute=0, second=0, microsecond=0)

    country_suffix = f"?country={CountryID.Germany}"

    layers.append(
        MapLayer(
            url=f"/stations/map/current{country_suffix}",
            timestamp=to_timestamp(now),
            observation=ObservationType.Recent,
        ),
    )

    # Forecast
    soon = now + timedelta(hours=2)
    soon_timestamp = to_timestamp(soon)
    layers.append(
        MapLayer(
            url=f"/stations/map/{soon_timestamp}{country_suffix}",
            timestamp=soon_timestamp,
            observation=ObservationType.Forecast,
        ),
    )

    # Today
    start = now.replace(hour=0)
    for i in range(1, 8):  # pragma: no cover
        time = start + timedelta(hours=i * 3)
        if time <= soon:
            continue
        timestamp = to_timestamp(time)
        layers.append(
            MapLayer(
                url=f"/stations/map/{timestamp}{country_suffix}",
                timestamp=timestamp,
                observation=ObservationType.Forecast,
            ),
        )

    # 7 days
    start = now + timedelta(hours=24 - now.hour)
    for i in range(28):
        time = start + timedelta(hours=i * 6)
        timestamp = to_timestamp(time)
        layers.append(
            MapLayer(
                url=f"/stations/map/{timestamp}{country_suffix}",
                timestamp=timestamp,
                observation=ObservationType.Forecast,
            ),
        )

    return layers, []


async def get_map_precipitation() -> tuple[list[MapLayer], list[float]]:
    """Get DWD precipitation map layers."""
    layers: list[MapLayer] = []

    current_time = datetime.now(tz=UTC)
    current_now = current_time.astimezone()
    utc_delta = current_now.utcoffset()
    utc_delta_seconds = 0.0
    if utc_delta:  # pragma: no cover
        utc_delta_seconds = utc_delta.seconds
    time_delta = timedelta(
        minutes=current_time.minute % 5,
        seconds=current_time.second,
        microseconds=current_time.microsecond,
    )
    current_time -= time_delta
    if (
        time_delta.seconds < PRECIPITATION_BUFFER_SECONDS
    ):  # buffer for recent image # pragma: no cover
        current_time -= timedelta(minutes=5)
    test_time = current_time.replace(tzinfo=None).isoformat()
    test_url = (
        f"{MAPS_BASEURL}&layers=dwd:RX-Produkt&bbox=5,50,6,51"
        f"&width=100&height=100&time={test_time}.000Z"
    )

    logger.debug(MESSAGE_MAP_URL, test_url)

    async with AsyncClient() as client:
        response = await client.get(test_url, timeout=MAPS_TIMEOUT)

    if "InvalidDimensionValue" in response.text:  # pragma: no cover
        logger.info(MESSAGE_NOT_AVAILABLE_YET)
        current_time -= timedelta(minutes=5)

    most_recent = current_time.isoformat()

    # historical data + recent
    for i in range(18, -1, -1):
        time = current_time - timedelta(minutes=5 * i)
        time = time.replace(tzinfo=None)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta_seconds)
        url = (
            f"{MAPS_BASEURL}&layers=dwd:RX-Produkt&width=512&height=512"
            f"&time={time_string}.000Z"
        )
        layers.append(
            MapLayer(
                url=url,
                timestamp=to_timestamp(time),
                observation=ObservationType.Historical
                if i != 0
                else ObservationType.Recent,
            ),
        )
        most_recent = time_string
    # forecast
    for i in range(1, 19, 1):
        time = current_time + timedelta(minutes=5 * i)
        time = time.replace(tzinfo=None)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta_seconds)
        url = (
            f"{MAPS_BASEURL}&layers=dwd:WN-Produkt&width=512&height=512"
            f"&time={time_string}.000Z&cache={most_recent}.000Z"
        )
        layers.append(
            MapLayer(
                url=url,
                timestamp=to_timestamp(time),
                observation=ObservationType.Forecast,
            ),
        )

    return layers, []


async def get_map_temperature() -> tuple[list[MapLayer], list[float]]:
    """Get DWD temperature map layers."""
    layers: list[MapLayer] = []

    current_time = datetime.now(tz=UTC)
    current_now = current_time.astimezone()
    utc_delta = current_now.utcoffset()
    utc_delta_seconds = 0.0
    if utc_delta:  # pragma: no cover
        utc_delta_seconds = utc_delta.seconds
    time_delta = timedelta(
        minutes=current_time.minute,
        seconds=current_time.second,
        microseconds=current_time.microsecond,
    )
    current_time -= time_delta
    test_time = current_time.replace(tzinfo=None).isoformat()
    test_url = (
        f"{MAPS_BASEURL}&layers=dwd:Icon-eu_reg00625_fd_gl_T&bbox=5,50,6,51"
        f"&width=100&height=100&time={test_time}.000Z"
    )

    logger.debug(MESSAGE_MAP_URL, test_url)

    async with AsyncClient() as client:
        response = await client.get(test_url, timeout=MAPS_TIMEOUT)

    if "InvalidDimensionValue" in response.text:  # pragma: no cover
        logger.info(MESSAGE_NOT_AVAILABLE_YET)
        current_time += timedelta(hours=1)

    for i in range(24):
        time = current_time + timedelta(hours=i)
        time = time.replace(tzinfo=None)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta_seconds)
        url = (
            f"{MAPS_BASEURL}&layers=dwd:Icon-eu_reg00625_fd_gl_T&width=512&height=512"
            f"&time={time_string}.000Z"
        )

        layers.append(
            MapLayer(
                url=url,
                timestamp=to_timestamp(time),
                observation=ObservationType.Forecast,
            ),
        )

    return layers, []


async def get_map_uv(map_type: MapType) -> tuple[list[MapLayer], list[float]]:
    """Get DWD UV map layers."""
    layers: list[MapLayer] = []

    map_name = "dwd:UVIndex" if map_type == MapType.UVIndexMax else "dwd:UV_Dosis_EU_CL"
    map_style = "uvi_cs" if map_type == MapType.UVIndexMax else ""

    current_time = datetime.now(tz=UTC)
    current_now = current_time.astimezone()
    utc_delta = current_now.utcoffset()
    utc_delta_seconds = 0.0
    if utc_delta:  # pragma: no cover
        utc_delta_seconds = utc_delta.seconds
    current_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    test_time = current_time.replace(tzinfo=None).isoformat()
    test_url = (
        f"{MAPS_BASEURL}&layers={map_name}&styles={map_style}&bbox=5,50,6,51"
        f"&width=100&height=100&time={test_time}.000Z"
    )

    logger.debug(MESSAGE_MAP_URL, test_url)

    async with AsyncClient() as client:
        response = await client.get(test_url, timeout=MAPS_TIMEOUT)

    if "InvalidDimensionValue" in response.text:  # pragma: no cover
        logger.info(MESSAGE_NOT_AVAILABLE_YET)
        current_time -= timedelta(days=1)

    # forecast
    for i in range(3):
        time = current_time + timedelta(days=i)
        time = time.replace(tzinfo=None)
        time_string = time.isoformat()
        url = (
            f"{MAPS_BASEURL}&layers={map_name}&styles={map_style}"
            f"&width=512&height=512&time={time_string}.000Z"
        )
        time += timedelta(seconds=utc_delta_seconds)
        layers.append(
            MapLayer(
                url=url,
                timestamp=to_timestamp(time),
                observation=ObservationType.Forecast,
            ),
        )

    return layers, []


async def get_map_layers(map_type: MapType) -> tuple[list[MapLayer], list[float]]:
    """Get DWD map layers."""
    if map_type == MapType.WeatherCondition:
        return get_map_condition()

    if map_type == MapType.Precipitation:
        return await get_map_precipitation()

    if map_type == MapType.PrecipitationGlobal:
        return await get_global_map_precipitation()

    if map_type == MapType.CloudCoverageInfraredGlobal:
        return await get_global_map_cloud_infrared()

    if map_type == MapType.Temperature:
        return await get_map_temperature()

    if map_type in {MapType.UVIndexMax, MapType.UVDose}:
        return await get_map_uv(map_type)

    raise UnsupportedMapTypeException


def get_map_legend(map_type: MapType) -> MapLegend:
    """Get DWD map legend."""
    if map_type == MapType.PrecipitationGlobal:
        return get_librewxr_map_legend(map_type)

    if map_type == MapType.Precipitation:
        items = [
            MapLegendItem(value="", color="transparent", placeholder=True),
            MapLegendItem(value="0", color="transparent"),
            MapLegendItem(value="7", color="#97F9FC"),
            MapLegendItem(value="10", color="#6CF8FC"),
            MapLegendItem(value="12", color="#58CBCA"),
            MapLegendItem(value="15", color="#489A36"),
            MapLegendItem(value="19", color="#5CBF1C"),
            MapLegendItem(value="24", color="#99CD1B"),
            MapLegendItem(value="28", color="#CCE628"),
            MapLegendItem(value="33", color="#FDF734"),
            MapLegendItem(value="37", color="#F9C432"),
            MapLegendItem(value="42", color="#F28831"),
            MapLegendItem(value="46", color="#ED462F"),
            MapLegendItem(value="51", color="#B53322"),
            MapLegendItem(value="55", color="#4A4CFB"),
            MapLegendItem(value="60", color="#173ACA"),
            MapLegendItem(value="65", color="#9B3C99"),
            MapLegendItem(value="75", color="#EA64FE"),
            MapLegendItem(value="85", color="#000000"),
            MapLegendItem(value="dBZ", color="transparent", placeholder=True),
        ]
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.Temperature:
        items = [
            MapLegendItem(value="", color="transparent", placeholder=True),
            MapLegendItem(value="", color="#9168A3"),
            MapLegendItem(value="-7.5", color="#8172A8"),
            MapLegendItem(value="-2.5", color="#8292bC"),
            MapLegendItem(value="2.5", color="#86B1D1"),
            MapLegendItem(value="7.5", color="#96C7E3"),
            MapLegendItem(value="12.5", color="#E6E6E6"),
            MapLegendItem(value="17.5", color="#F7D640"),
            MapLegendItem(value="22.5", color="#D0AF65"),
            MapLegendItem(value="27.5", color="#ED9C67"),
            MapLegendItem(value="32.5", color="#EB8963"),
            MapLegendItem(value="37.5", color="#E87C66"),
            MapLegendItem(value="°C", color="transparent", placeholder=True),
        ]
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.UVIndexMax:
        items = [
            MapLegendItem(value="", color="transparent", placeholder=True),
            MapLegendItem(value="0", color="#000000"),
            MapLegendItem(value="1", color="#4FB400"),
            MapLegendItem(value="2", color="#A0CE01"),
            MapLegendItem(value="3", color="#F7E500"),
            MapLegendItem(value="4", color="#F8B700"),
            MapLegendItem(value="5", color="#F88800"),
            MapLegendItem(value="6", color="#F85B00"),
            MapLegendItem(value="7", color="#E72D0D"),
            MapLegendItem(value="8", color="#D8011D"),
            MapLegendItem(value="9", color="#FF0097"),
            MapLegendItem(value="10", color="#B34CFF"),
            MapLegendItem(value="11", color="#998CFF"),
            MapLegendItem(value="12", color="#D48CBD"),
            MapLegendItem(value="13", color="#EAA8D3"),
            MapLegendItem(value="UV", color="transparent", placeholder=True),
        ]
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.UVDose:
        items = [
            MapLegendItem(value="", color="transparent", placeholder=True),
            MapLegendItem(value="0", color="#1332FF"),
            MapLegendItem(value="0.25", color="#00B49F"),
            MapLegendItem(value="1.25", color="#02FE01"),
            MapLegendItem(value="2.5", color="#009700"),
            MapLegendItem(value="5.0", color="#FCFF6E"),
            MapLegendItem(value="6.25", color="#F6BD0C"),
            MapLegendItem(value="7.5", color="#FF311D"),
            MapLegendItem(value="8.75", color="#FF96FF"),
            MapLegendItem(value="10.0", color="#FFC5FF"),
            MapLegendItem(value="kJ/m²", color="transparent", placeholder=True),
        ]
        return MapLegend(map_type=map_type, items=items)

    raise UnsupportedMapTypeException


def get_all_map_legends() -> list[MapLegend]:
    """Get all DWD map legends."""
    supported = get_supported_map_types()
    return [get_map_legend(t.map_type) for t in supported if t.has_legend]


async def get_weather_map(map_id: str) -> list[WeatherInfoExtended]:
    """Get weather map from ID."""
    timestamp = map_id
    if map_id == "current":
        now = datetime.now(tz=UTC)
        now = now.replace(minute=0, second=0, microsecond=0)
        timestamp = to_timestamp(now)

    logger.debug("DWD MOSMIX timestamp: %s", timestamp)

    ids: set[str] = await get_mosmix_ids_for_timestamp(timestamp)
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
