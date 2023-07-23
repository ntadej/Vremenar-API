"""DWD weather stations."""
from datetime import datetime, timedelta, timezone

from httpx import AsyncClient

from vremenar.database.stations import get_stations
from vremenar.definitions import CountryID, ObservationType
from vremenar.exceptions import InvalidSearchQueryException, UnknownStationException
from vremenar.models.stations import (
    StationInfo,
    StationInfoExtended,
    StationSearchModel,
)
from vremenar.models.weather import WeatherCondition, WeatherInfoExtended
from vremenar.utils import join_url, logger, parse_time, to_timestamp

from .utils import get_icon, parse_source

BRIGHTSKY_BASEURL = "https://api.brightsky.dev"


async def list_stations() -> list[StationInfoExtended]:
    """List DWD weather stations."""
    stations = await get_stations(CountryID.Germany)
    return list(stations.values())


async def _process_find_station(url: str) -> list[StationInfo]:
    """Process find station request."""
    logger.debug("Brightsky URL: %s", url)

    locations: list[StationInfo] = []

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if "sources" not in response_body:  # pragma: no cover
        raise UnknownStationException()

    for source in response_body["sources"]:
        station = await parse_source(source)
        if not station:  # pragma: no cover
            continue

        locations.append(station)
        break

    return locations


async def find_station(
    query: StationSearchModel,
    include_forecast_only: bool,
) -> list[StationInfo]:
    """Find station by coordinate or string."""
    url_forecast: str = join_url(BRIGHTSKY_BASEURL, "weather", trailing_slash=False)
    url_current: str = join_url(
        BRIGHTSKY_BASEURL,
        "current_weather",
        trailing_slash=False,
    )

    if query.string:
        err = "Only coordinates are required"
        raise InvalidSearchQueryException(err)

    if query.latitude is not None and query.longitude is not None:
        url_forecast += f"?lat={query.latitude}&lon={query.longitude}"
        url_current += f"?lat={query.latitude}&lon={query.longitude}"
    else:
        err = "Only coordinates are required"
        raise InvalidSearchQueryException(err)

    locations: list[StationInfo] = []
    if include_forecast_only:
        today = datetime.now(tz=timezone.utc).date()
        target_date = today + timedelta(days=2)
        url_forecast += (
            f'&date={target_date.strftime("%Y-%m-%d")}'
            f'&last_date={target_date.strftime("%Y-%m-%d")}'
        )

        locations = await _process_find_station(url_forecast)

    if not locations or locations[0].forecast_only:
        locations += await _process_find_station(url_current)

    return locations


async def current_station_condition(station_id: str) -> WeatherInfoExtended:
    """Get current station weather condition."""
    stations = await get_stations(CountryID.Germany)
    station: StationInfoExtended | None = stations.get(station_id, None)
    if not station:
        raise UnknownStationException()

    url: str = join_url(BRIGHTSKY_BASEURL, "current_weather", trailing_slash=False)
    url += f"?lat={station.coordinate.latitude}&lon={station.coordinate.longitude}"

    logger.debug("Brightsky URL: %s", url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if "sources" not in response_body:  # pragma: no cover
        raise UnknownStationException()

    for source in response_body["sources"]:
        station = await parse_source(source)
        break

    if not station:  # pragma: no cover
        raise UnknownStationException()

    weather = response_body["weather"]

    time = parse_time(weather["timestamp"])

    condition = WeatherCondition(
        observation=ObservationType.Recent,
        timestamp=to_timestamp(time),
        icon=get_icon(weather, station, time),
        temperature=weather["temperature"],
    )

    return WeatherInfoExtended(station=station, condition=condition)
