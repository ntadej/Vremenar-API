"""Weather conditions map API."""

from fastapi import APIRouter
from typing import List

from ..definitions import CountryID
from ..models.weather import WeatherInfo
from ..sources import get_weather_map

router = APIRouter()


@router.get('/weather_map/{id}', tags=['weather_map'])
async def weather_map(country: CountryID, id: str) -> List[WeatherInfo]:
    """Get weather conditions map for a specific ID."""
    return await get_weather_map(country, id)
