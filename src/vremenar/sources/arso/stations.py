"""ARSO weather stations."""

from fastapi import HTTPException, status
from functools import lru_cache
from httpx import AsyncClient
from typing import Optional

from ...definitions import ObservationType
from ...models.stations import StationInfo, StationInfoExtended, StationSearchModel
from ...models.weather import WeatherInfoExtended
from ...utils import join_url, logger

from .utils import API_BASEURL, TIMEOUT, get_stations, parse_feature, parse_station


@lru_cache
def list_stations() -> list[StationInfoExtended]:
    """List ARSO weather stations."""
    return list(get_stations().values())


async def find_station(query: StationSearchModel) -> list[StationInfo]:
    """Find station by coordinate or string."""
    url: str = join_url(API_BASEURL, 'locations', trailing_slash=True)

    if query.string and (query.latitude or query.longitude):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Either search string or coordinates are required',
        )

    if query.string:
        single = False
        url += f'?loc={query.string}'
    elif query.latitude is not None and query.longitude is not None:
        single = True
        url += f'?lat={query.latitude}&lon={query.longitude}'
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Either search string or coordinates are required',
        )

    logger.debug('ARSO URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url, timeout=TIMEOUT)

    response_body = response.json()

    if single:
        station = parse_station(response_body)
        if station:
            return [station]

    if 'features' not in response_body:  # pragma: no cover
        return []

    locations: list[StationInfo] = []
    for feature in response_body['features']:
        station = parse_station(feature)
        if station:
            locations.append(station)

    return locations


async def current_station_condition(station_id: str) -> WeatherInfoExtended:
    """Get current station weather condition."""
    stations = get_stations()
    station: Optional[StationInfoExtended] = stations.get(station_id, None)
    if not station:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    url = (
        join_url(API_BASEURL, 'locations', trailing_slash=True) + f'?loc={station.name}'
    )

    logger.debug('ARSO URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url, timeout=TIMEOUT)

    response_body = response.json()
    if 'features' not in response_body:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    for feature in response_body['features']:
        _, condition = parse_feature(feature, ObservationType.Recent)
        return WeatherInfoExtended(station=station, condition=condition)

    raise HTTPException(  # pragma: no cover
        status_code=status.HTTP_404_NOT_FOUND,
        detail='Unknown station',
    )
