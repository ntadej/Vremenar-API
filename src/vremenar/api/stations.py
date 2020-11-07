"""Weather stations API."""

from fastapi import APIRouter
from typing import List

from ..definitions import CountryID
from ..models.stations import StationSearchModel
from ..models.weather import WeatherInfo
from ..sources import find_station

router = APIRouter()


@router.post('/stations/find', tags=['stations'])
async def find(country: CountryID, query: StationSearchModel) -> List[WeatherInfo]:
    """Find weather station."""
    return await find_station(country, query)
