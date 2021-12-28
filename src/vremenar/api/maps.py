"""Weather map layers API."""

from fastapi import APIRouter

from .config import defaults
from ..definitions import CountryID
from ..models.maps import MapLayersList, MapLegend, MapType, SupportedMapType
from ..sources import (
    get_all_supported_map_types,
    get_map_layers,
    get_map_legend,
    get_all_map_legends,
)

router = APIRouter()


@router.get(
    '/maps/types',
    tags=['maps'],
    response_description='Get the supported map types',
    response_model=list[SupportedMapType],
    **defaults,
)
async def supported_map_types(country: CountryID) -> list[SupportedMapType]:
    """Get all supported map types for a specific country."""
    return get_all_supported_map_types(country)


@router.get(
    '/maps/list/{map_type}',
    tags=['maps'],
    response_description='Get list of maps per type',
    response_model=MapLayersList,
    **defaults,
)
async def map_layers(country: CountryID, map_type: MapType) -> MapLayersList:
    """Get list of maps per type for a specific country."""
    layers, bbox = await get_map_layers(country, map_type)
    return MapLayersList.init(map_type, bbox, layers)


@router.get(
    '/maps/legend',
    tags=['maps'],
    response_description='Get the legend for all map types',
    response_model=list[MapLegend],
    **defaults,
)
async def all_map_legends(country: CountryID) -> list[MapLegend]:
    """Get all map legends for a specific country."""
    return get_all_map_legends(country)


@router.get(
    '/maps/legend/{map_type}',
    tags=['maps'],
    response_description='Get the legend for a map type',
    response_model=MapLegend,
    **defaults,
)
async def map_legend(country: CountryID, map_type: MapType) -> MapLegend:
    """Get map legends per type for a specific country."""
    return get_map_legend(country, map_type)
