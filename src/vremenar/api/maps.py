"""Weather map layers API."""

from fastapi import APIRouter

from ..definitions import CountryID
from ..models.maps import MapResponse, MapType
from ..sources import get_map_layers

router = APIRouter()


@router.get('/maps/{map_type}', tags=['maps'])
async def map_layers(country: CountryID, map_type: MapType) -> MapResponse:
    """Get list of maps per type for a specific country."""
    layers, bbox = await get_map_layers(country, map_type)
    return MapResponse(map_type, bbox, layers)
