"""Weather stations API."""

from fastapi import APIRouter
from typing import List

from .config import defaults
from ..definitions import CountryID
from ..models.stations import ExtendedStationInfo, StationInfo, StationSearchModel
from ..sources import find_station

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
