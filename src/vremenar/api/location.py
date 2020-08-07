"""Weather conditions map API."""

from fastapi import APIRouter
from typing import List, Optional

from ..definitions import CountryID
from ..models.weather import WeatherInfo
from ..sources import find_location

router = APIRouter()


@router.post('/location/find', tags=['location'])
async def find(
    country: CountryID,
    string: Optional[str] = None,
    latitude: Optional[float] = None,
    longitude: Optional[float] = None,
) -> List[WeatherInfo]:
    """Get weather conditions map for a specific ID."""
    return await find_location(country, string, latitude, longitude)
