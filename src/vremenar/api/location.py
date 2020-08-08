"""Weather conditions map API."""

from fastapi import APIRouter, Body
from typing import List, Optional

from ..definitions import CountryID
from ..models.weather import WeatherInfo
from ..sources import find_location

router = APIRouter()
_empty_body = Body(None)


@router.post('/location/find', tags=['location'])
async def find(
    country: CountryID,
    string: Optional[str] = _empty_body,
    latitude: Optional[float] = _empty_body,
    longitude: Optional[float] = _empty_body,
) -> List[WeatherInfo]:
    """Get weather conditions map for a specific ID."""
    return await find_location(country, string, latitude, longitude)
