"""ARSO weather stations."""
from httpx import AsyncClient

from ...database.stations import get_stations
from ...definitions import CountryID, ObservationType
from ...exceptions import UnknownStationException, InvalidSearchQueryException
from ...models.stations import StationInfo, StationInfoExtended, StationSearchModel
from ...models.weather import WeatherInfoExtended
from ...utils import join_url, logger

from .utils import API_BASEURL, TIMEOUT, parse_feature, parse_station


async def list_stations() -> list[StationInfoExtended]:
    """List ARSO weather stations."""
    stations = await get_stations(CountryID.Slovenia)
    return list(stations.values())


async def find_station(query: StationSearchModel) -> list[StationInfo]:
    """Find station by coordinate or string."""
    url: str = join_url(API_BASEURL, "locations", trailing_slash=True)

    if query.string and (query.latitude or query.longitude):
        err = "Either search string or coordinates are required"
        raise InvalidSearchQueryException(err)

    if query.string:
        single = False
        url += f"?loc={query.string}"
    elif query.latitude is not None and query.longitude is not None:
        single = True
        url += f"?lat={query.latitude}&lon={query.longitude}"
    else:
        err = "Either search string or coordinates are required"
        raise InvalidSearchQueryException(err)

    logger.debug("ARSO URL: %s", url)

    async with AsyncClient() as client:
        response = await client.get(url, timeout=TIMEOUT)

    response_body = response.json()

    if single:
        station = await parse_station(response_body)
        if station:
            return [station]

    if "features" not in response_body:  # pragma: no cover
        return []

    locations: list[StationInfo] = []
    for feature in response_body["features"]:
        station = await parse_station(feature)
        if station:
            locations.append(station)

    return locations


async def current_station_condition(station_id: str) -> WeatherInfoExtended:
    """Get current station weather condition."""
    stations = await get_stations(CountryID.Slovenia)
    station: StationInfoExtended | None = stations.get(station_id, None)
    if not station:
        raise UnknownStationException()

    url = (
        join_url(API_BASEURL, "locations", trailing_slash=True) + f"?loc={station.name}"
    )

    logger.debug("ARSO URL: %s", url)

    async with AsyncClient() as client:
        response = await client.get(url, timeout=TIMEOUT)

    response_body = response.json()
    if "features" not in response_body:  # pragma: no cover
        raise UnknownStationException()

    for feature in response_body["features"]:
        _, condition = await parse_feature(feature, ObservationType.Recent)
        return WeatherInfoExtended(station=station, condition=condition)

    raise UnknownStationException()  # pragma: no cover
