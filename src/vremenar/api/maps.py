"""Weather map layers API."""

from fastapi import APIRouter

from .config import defaults
from ..definitions import CountryID
from ..models.maps import MapLayersList, MapType
from ..sources import get_map_layers

router = APIRouter()


@router.get(
    '/maps/{map_type}',
    tags=['maps'],
    response_description='Get list of maps per type',
    response_model=MapLayersList,
    **defaults,
)
async def map_layers(country: CountryID, map_type: MapType) -> MapLayersList:
    """Get list of maps per type for a specific country."""
    layers, bbox = await get_map_layers(country, map_type)
    return MapLayersList.init(map_type, bbox, layers)
