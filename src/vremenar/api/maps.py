"""Weather map layers API."""

from fastapi import APIRouter

from vremenar.definitions import CountryID
from vremenar.models.maps import MapLayersList, MapLegend, MapType, SupportedMapType
from vremenar.sources import (
    get_all_map_legends,
    get_all_supported_map_types,
    get_map_layers,
    get_map_legend,
)

from .config import defaults

router = APIRouter()


@router.get(
    "/maps/types",
    tags=["maps"],
    response_description="Get the supported map types",
    **defaults,
)
async def supported_map_types(country: CountryID) -> list[SupportedMapType]:
    """Get all supported map types for a specific country."""
    return get_all_supported_map_types(country)


@router.get(
    "/maps/list/{map_type}",
    tags=["maps"],
    response_description="Get list of maps per type",
    **defaults,
)
async def map_layers(country: CountryID, map_type: MapType) -> MapLayersList:
    """Get list of maps per type for a specific country."""
    layers, bbox = await get_map_layers(country, map_type)
    return MapLayersList.init(map_type, bbox, layers)


@router.get(
    "/maps/legend",
    tags=["maps"],
    response_description="Get the legend for all map types",
    **defaults,
)
async def all_map_legends(country: CountryID) -> list[MapLegend]:
    """Get all map legends for a specific country."""
    return get_all_map_legends(country)


@router.get(
    "/maps/legend/{map_type}",
    tags=["maps"],
    response_description="Get the legend for a map type",
    **defaults,
)
async def map_legend(country: CountryID, map_type: MapType) -> MapLegend:
    """Get map legends per type for a specific country."""
    return get_map_legend(country, map_type)
