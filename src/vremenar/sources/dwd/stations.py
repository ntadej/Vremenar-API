"""DWD weather stations."""

from fastapi import HTTPException, status
from functools import lru_cache
from httpx import AsyncClient
from typing import Optional

from ...definitions import ObservationType
from ...models.stations import StationInfo, StationInfoExtended, StationSearchModel
from ...models.weather import WeatherCondition, WeatherInfoExtended
from ...utils import join_url, logger, parse_time, to_timestamp

from .utils import get_icon, get_stations, parse_source

BRIGHTSKY_BASEURL = 'https://api.brightsky.dev'


@lru_cache
def list_stations() -> list[StationInfoExtended]:
    """List DWD weather stations."""
    return list(get_stations().values())


async def find_station(query: StationSearchModel) -> list[StationInfo]:
    """Find station by coordinate or string."""
    url: str = join_url(BRIGHTSKY_BASEURL, 'current_weather', trailing_slash=False)

    if query.string:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Only coordinates are required',
        )

    if query.latitude is not None and query.longitude is not None:
        url += f'?lat={query.latitude}&lon={query.longitude}'
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail='Only coordinates are required',
        )

    logger.debug('Brightsky URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if 'sources' not in response_body:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    locations: list[StationInfo] = []
    for source in response_body['sources']:
        station = parse_source(source)
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

    url: str = join_url(BRIGHTSKY_BASEURL, 'current_weather', trailing_slash=False)
    url += f'?lat={station.coordinate.latitude}&lon={station.coordinate.longitude}'

    logger.debug('Brightsky URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if 'sources' not in response_body:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    for source in response_body['sources']:
        station = parse_source(source)
        break

    if not station:  # pragma: no cover
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail='Unknown station',
        )

    weather = response_body['weather']

    time = parse_time(weather['timestamp'])

    condition = WeatherCondition(
        observation=ObservationType.Recent,
        timestamp=to_timestamp(time),
        icon=get_icon(station, weather, time),
        temperature=weather['temperature'],
    )

    return WeatherInfoExtended(station=station, condition=condition)
