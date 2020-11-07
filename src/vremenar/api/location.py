"""Weather conditions map API."""

from fastapi import APIRouter
from typing import List

from ..definitions import CountryID
from ..models.location import LocationSearchModel
from ..models.weather import WeatherInfo
from ..sources import find_location

router = APIRouter()


@router.post('/location/find', tags=['location'])
async def find(country: CountryID, query: LocationSearchModel) -> List[WeatherInfo]:
    """Get weather conditions map for a specific ID."""
    return await find_location(country, query.string, query.latitude, query.longitude)
