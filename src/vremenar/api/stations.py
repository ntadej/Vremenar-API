"""Weather stations API."""

from fastapi import APIRouter
from typing import List

from .config import defaults
from ..definitions import CountryID
from ..models.maps import WeatherInfo
from ..models.stations import ExtendedStationInfo, StationInfo, StationSearchModel
from ..sources import find_station, get_weather_map

router = APIRouter()


@router.get(
    '/stations/list',
    tags=['stations'],
    response_description='List of weather stations',
    response_model=List[StationInfo],
    **defaults,
)
async def list(county: CountryID) -> List[StationInfo]:
    """List weather stations."""
    return []


@router.post(
    '/stations/find',
    tags=['stations'],
    response_description='List of weather stations with current weather condition',
    response_model=List[ExtendedStationInfo],
    **defaults,
)
async def find(
    country: CountryID, query: StationSearchModel
) -> List[ExtendedStationInfo]:
    """Find weather station."""
    return await find_station(country, query)


@router.get(
    '/stations/map/{id}',
    tags=['stations'],
    response_description='List of weather information',
    response_model=List[WeatherInfo],
    **defaults,
)
async def map(country: CountryID, id: str) -> List[WeatherInfo]:
    """Get weather conditions map for a specific ID."""
    return await get_weather_map(country, id)
