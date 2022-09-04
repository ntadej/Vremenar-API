"""DWD weather stations."""
from datetime import date, timedelta
from httpx import AsyncClient
from typing import Optional

from ...database.stations import get_stations
from ...definitions import CountryID, ObservationType
from ...exceptions import UnknownStationException, InvalidSearchQueryException
from ...models.stations import StationInfo, StationInfoExtended, StationSearchModel
from ...models.weather import WeatherCondition, WeatherInfoExtended
from ...utils import join_url, logger, parse_time, to_timestamp

from .utils import get_icon, parse_source

BRIGHTSKY_BASEURL = 'https://api.brightsky.dev'


async def list_stations() -> list[StationInfoExtended]:
    """List DWD weather stations."""
    stations = await get_stations(CountryID.Germany)
    return list(stations.values())


async def find_station(
    query: StationSearchModel, include_forecast_only: bool
) -> list[StationInfo]:
    """Find station by coordinate or string."""
    url_forecast: str = join_url(BRIGHTSKY_BASEURL, 'weather', trailing_slash=False)
    url_current: str = join_url(
        BRIGHTSKY_BASEURL, 'current_weather', trailing_slash=False
    )

    if query.string:
        raise InvalidSearchQueryException('Only coordinates are required')

    if query.latitude is not None and query.longitude is not None:
        url_forecast += f'?lat={query.latitude}&lon={query.longitude}'
        url_current += f'?lat={query.latitude}&lon={query.longitude}'
    else:
        raise InvalidSearchQueryException('Only coordinates are required')

    locations: list[StationInfo] = []
    if include_forecast_only:
        today = date.today()
        target_date = today + timedelta(days=2)
        url_forecast += (
            f'&date={target_date.strftime("%Y-%m-%d")}'
            f'&last_date={target_date.strftime("%Y-%m-%d")}'
        )

        logger.debug('Brightsky URL forecast: %s', url_forecast)

        async with AsyncClient() as client:
            response = await client.get(url_forecast)

        response_body = response.json()
        if 'sources' not in response_body:  # pragma: no cover
            raise UnknownStationException()

        for source in response_body['sources']:
            station = await parse_source(source)
            if station:
                locations.append(station)
                break

    if not locations or locations[0].forecast_only:
        logger.debug('Brightsky URL current: %s', url_current)

        async with AsyncClient() as client:
            response = await client.get(url_current)

        response_body = response.json()
        if 'sources' not in response_body:  # pragma: no cover
            raise UnknownStationException()

        for source in response_body['sources']:
            station = await parse_source(source)
            if station:
                locations.append(station)
                break

    return locations


async def current_station_condition(station_id: str) -> WeatherInfoExtended:
    """Get current station weather condition."""
    stations = await get_stations(CountryID.Germany)
    station: Optional[StationInfoExtended] = stations.get(station_id, None)
    if not station:
        raise UnknownStationException()

    url: str = join_url(BRIGHTSKY_BASEURL, 'current_weather', trailing_slash=False)
    url += f'?lat={station.coordinate.latitude}&lon={station.coordinate.longitude}'

    logger.debug('Brightsky URL: %s', url)

    async with AsyncClient() as client:
        response = await client.get(url)

    response_body = response.json()
    if 'sources' not in response_body:  # pragma: no cover
        raise UnknownStationException()

    for source in response_body['sources']:
        station = await parse_source(source)
        break

    if not station:  # pragma: no cover
        raise UnknownStationException()

    weather = response_body['weather']

    time = parse_time(weather['timestamp'])

    condition = WeatherCondition(
        observation=ObservationType.Recent,
        timestamp=to_timestamp(time),
        icon=get_icon(station, weather, time),
        temperature=weather['temperature'],
    )

    return WeatherInfoExtended(station=station, condition=condition)
