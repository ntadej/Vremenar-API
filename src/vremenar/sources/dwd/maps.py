"""DWD weather maps."""
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

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
from vremenar.utils import logger, to_timestamp

from .utils import get_mosmix_ids_for_timestamp, get_mosmix_records, parse_record

MAPS_BASEURL = (
    "https://maps.dwd.de/geoserver/dwd/ows"
    "?service=WMS&version=1.3&request=GetMap&srs=EPSG:3857&format=image%2Fpng&transparent=true"
)

MESSAGE_MAP_URL = "DWD Map URL: %s"
MESSAGE_NOT_AVAILABLE_YET = "Map not available yet"


def get_supported_map_types() -> list[SupportedMapType]:
    """Get DWD supported map types."""
    return [
        SupportedMapType(
            map_type=MapType.WeatherCondition,
            rendering_type=MapRenderingType.Icons,
        ),
        SupportedMapType(
            map_type=MapType.Precipitation,
            rendering_type=MapRenderingType.Tiles,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.Temperature,
            rendering_type=MapRenderingType.Tiles,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.UVIndexMax,
            rendering_type=MapRenderingType.Tiles,
            has_legend=True,
        ),
        SupportedMapType(
            map_type=MapType.UVDose,
            rendering_type=MapRenderingType.Tiles,
            has_legend=True,
        ),
    ]


def get_map_condition() -> tuple[list[MapLayer], list[float]]:
    """Get DWD condition map layers."""
    layers: list[MapLayer] = []

    now = datetime.now(tz=timezone.utc)
    now = now.replace(minute=0, second=0, microsecond=0)

    country_suffix = f"?country={CountryID.Germany.value}"

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

    current_time = datetime.now(tz=timezone.utc)
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
    if time_delta.seconds < 100:  # buffer for recent image # pragma: no cover
        current_time -= timedelta(minutes=5)
    test_time = current_time.isoformat()
    test_url = (
        f"{MAPS_BASEURL}&layers=dwd:RX-Produkt&bbox=5,50,6,51"
        f"&width=100&height=100&time={test_time}.000Z"
    )

    logger.debug(MESSAGE_MAP_URL, test_url)

    async with AsyncClient() as client:
        response = await client.get(test_url)

    if "InvalidDimensionValue" in response.text:  # pragma: no cover
        logger.info(MESSAGE_NOT_AVAILABLE_YET)
        current_time -= timedelta(minutes=5)

    # historical data + recent
    for i in range(18, -1, -1):
        time = current_time - timedelta(minutes=5 * i)
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
    # forecast
    for i in range(1, 19, 1):
        time = current_time + timedelta(minutes=5 * i)
        time_string = time.isoformat()
        time += timedelta(seconds=utc_delta_seconds)
        url = (
            f"{MAPS_BASEURL}&layers=dwd:WN-Produkt&width=512&height=512"
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


async def get_map_temperature() -> tuple[list[MapLayer], list[float]]:
    """Get DWD temperature map layers."""
    layers: list[MapLayer] = []

    current_time = datetime.now(tz=timezone.utc)
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
    test_time = current_time.isoformat()
    test_url = (
        f"{MAPS_BASEURL}&layers=dwd:Icon-eu_reg00625_fd_gl_T&bbox=5,50,6,51"
        f"&width=100&height=100&time={test_time}.000Z"
    )

    logger.debug(MESSAGE_MAP_URL, test_url)

    async with AsyncClient() as client:
        response = await client.get(test_url)

    if "InvalidDimensionValue" in response.text:  # pragma: no cover
        logger.info(MESSAGE_NOT_AVAILABLE_YET)
        current_time += timedelta(hours=1)

    for i in range(24):
        time = current_time + timedelta(hours=i)
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

    current_time = datetime.now(tz=timezone.utc)
    current_now = current_time.astimezone()
    utc_delta = current_now.utcoffset()
    utc_delta_seconds = 0.0
    if utc_delta:  # pragma: no cover
        utc_delta_seconds = utc_delta.seconds
    current_time = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
    test_time = current_time.isoformat()
    test_url = (
        f"{MAPS_BASEURL}&layers={map_name}&styles={map_style}&bbox=5,50,6,51"
        f"&width=100&height=100&time={test_time}.000Z"
    )

    logger.debug(MESSAGE_MAP_URL, test_url)

    async with AsyncClient() as client:
        response = await client.get(test_url)

    if "InvalidDimensionValue" in response.text:  # pragma: no cover
        logger.info(MESSAGE_NOT_AVAILABLE_YET)
        current_time -= timedelta(days=1)

    # forecast
    for i in range(0, 3):
        time = current_time + timedelta(days=i)
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

    if map_type == MapType.Temperature:
        return await get_map_temperature()

    if map_type in (MapType.UVIndexMax, MapType.UVDose):
        return await get_map_uv(map_type)

    raise UnsupportedMapTypeException()


def get_map_legend(map_type: MapType) -> MapLegend:  # noqa: PLR0915
    """Get DWD map legend."""
    if map_type == MapType.Precipitation:
        items = []
        items.append(MapLegendItem(value="", color="transparent", placeholder=True))
        items.append(MapLegendItem(value="0", color="transparent"))
        items.append(MapLegendItem(value="7", color="#97F9FC"))
        items.append(MapLegendItem(value="10", color="#6CF8FC"))
        items.append(MapLegendItem(value="12", color="#58CBCA"))
        items.append(MapLegendItem(value="15", color="#489A36"))
        items.append(MapLegendItem(value="19", color="#5CBF1C"))
        items.append(MapLegendItem(value="24", color="#99CD1B"))
        items.append(MapLegendItem(value="28", color="#CCE628"))
        items.append(MapLegendItem(value="33", color="#FDF734"))
        items.append(MapLegendItem(value="37", color="#F9C432"))
        items.append(MapLegendItem(value="42", color="#F28831"))
        items.append(MapLegendItem(value="46", color="#ED462F"))
        items.append(MapLegendItem(value="51", color="#B53322"))
        items.append(MapLegendItem(value="55", color="#4A4CFB"))
        items.append(MapLegendItem(value="60", color="#173ACA"))
        items.append(MapLegendItem(value="65", color="#9B3C99"))
        items.append(MapLegendItem(value="75", color="#EA64FE"))
        items.append(MapLegendItem(value="85", color="#000000"))
        items.append(MapLegendItem(value="dBZ", color="transparent", placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.Temperature:
        items = []
        items.append(MapLegendItem(value="", color="transparent", placeholder=True))
        items.append(MapLegendItem(value="", color="#9168A3"))
        items.append(MapLegendItem(value="-7.5", color="#8172A8"))
        items.append(MapLegendItem(value="-2.5", color="#8292bC"))
        items.append(MapLegendItem(value="2.5", color="#86B1D1"))
        items.append(MapLegendItem(value="7.5", color="#96C7E3"))
        items.append(MapLegendItem(value="12.5", color="#E6E6E6"))
        items.append(MapLegendItem(value="17.5", color="#F7D640"))
        items.append(MapLegendItem(value="22.5", color="#D0AF65"))
        items.append(MapLegendItem(value="27.5", color="#ED9C67"))
        items.append(MapLegendItem(value="32.5", color="#EB8963"))
        items.append(MapLegendItem(value="37.5", color="#E87C66"))
        items.append(MapLegendItem(value="°C", color="transparent", placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.UVIndexMax:
        items = []
        items.append(MapLegendItem(value="", color="transparent", placeholder=True))
        items.append(MapLegendItem(value="0", color="#000000"))
        items.append(MapLegendItem(value="1", color="#4FB400"))
        items.append(MapLegendItem(value="2", color="#A0CE01"))
        items.append(MapLegendItem(value="3", color="#F7E500"))
        items.append(MapLegendItem(value="4", color="#F8B700"))
        items.append(MapLegendItem(value="5", color="#F88800"))
        items.append(MapLegendItem(value="6", color="#F85B00"))
        items.append(MapLegendItem(value="7", color="#E72D0D"))
        items.append(MapLegendItem(value="8", color="#D8011D"))
        items.append(MapLegendItem(value="9", color="#FF0097"))
        items.append(MapLegendItem(value="10", color="#B34CFF"))
        items.append(MapLegendItem(value="11", color="#998CFF"))
        items.append(MapLegendItem(value="12", color="#D48CBD"))
        items.append(MapLegendItem(value="13", color="#EAA8D3"))
        items.append(MapLegendItem(value="UV", color="transparent", placeholder=True))
        return MapLegend(map_type=map_type, items=items)

    if map_type == MapType.UVDose:
        items = []
        items.append(MapLegendItem(value="", color="transparent", placeholder=True))
        items.append(MapLegendItem(value="0", color="#1332FF"))
        items.append(MapLegendItem(value="0.25", color="#00B49F"))
        items.append(MapLegendItem(value="1.25", color="#02FE01"))
        items.append(MapLegendItem(value="2.5", color="#009700"))
        items.append(MapLegendItem(value="5.0", color="#FCFF6E"))
        items.append(MapLegendItem(value="6.25", color="#F6BD0C"))
        items.append(MapLegendItem(value="7.5", color="#FF311D"))
        items.append(MapLegendItem(value="8.75", color="#FF96FF"))
        items.append(MapLegendItem(value="10.0", color="#FFC5FF"))
        items.append(
            MapLegendItem(value="kJ/m²", color="transparent", placeholder=True),
        )
        return MapLegend(map_type=map_type, items=items)

    raise UnsupportedMapTypeException()


def get_all_map_legends() -> list[MapLegend]:
    """Get all DWD map legends."""
    supported = get_supported_map_types()
    return [get_map_legend(t.map_type) for t in supported if t.has_legend]


async def get_weather_map(map_id: str) -> list[WeatherInfoExtended]:
    """Get weather map from ID."""
    timestamp = map_id
    if map_id == "current":
        now = datetime.now(tz=timezone.utc)
        now = now.replace(minute=0, second=0, microsecond=0)
        timestamp = to_timestamp(now)

    logger.debug("DWD MOSMIX timestamp: %s", timestamp)

    ids: set[str] = await get_mosmix_ids_for_timestamp(timestamp)
    if not ids:
        raise UnrecognisedMapIDException()

    records = await get_mosmix_records(ids)

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
