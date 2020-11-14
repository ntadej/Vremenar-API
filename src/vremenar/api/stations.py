"""Weather stations API."""

from fastapi import APIRouter
from typing import List

from .config import defaults
from ..definitions import CountryID
from ..models.stations import StationInfo, StationSearchModel
from ..models.weather import WeatherInfo
from ..sources import (
    current_station_condition,
    find_station,
    get_weather_map,
    list_stations,
)

router = APIRouter()


@router.get(
    '/stations/list',
    tags=['stations'],
    name='List stations',
    response_description='List of weather stations',
    response_model=List[StationInfo],
    **defaults,
)
async def list(country: CountryID) -> List[StationInfo]:
    """List weather stations."""
    return list_stations(country)


@router.post(
    '/stations/find',
    tags=['stations'],
    name='Find stations',
    response_description='List of weather stations',
    response_model=List[StationInfo],
    **defaults,
)
async def find(country: CountryID, query: StationSearchModel) -> List[StationInfo]:
    """Find weather station."""
    return await find_station(country, query)


@router.get(
    '/stations/condition/{station_id}',
    tags=['stations'],
    name='Current station condition',
    response_description='Current weather condition for the chosen station',
    response_model=WeatherInfo,
    **defaults,
)
async def condition(country: CountryID, station_id: str) -> WeatherInfo:
    """Get current station condition."""
    return await current_station_condition(country, station_id)


@router.get(
    '/stations/map/{map_id}',
    tags=['stations'],
    name='Weather conditions map',
    response_description='List of weather information',
    response_model=List[WeatherInfo],
    **defaults,
)
async def map(country: CountryID, map_id: str) -> List[WeatherInfo]:
    """Get weather conditions map for a specific ID."""
    return await get_weather_map(country, map_id)
