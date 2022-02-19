"""Weather alerts API."""
from fastapi import APIRouter

from .config import defaults
from ..definitions import CountryID, LanguageID
from ..models.alerts import AlertAreaWithPolygon, AlertInfoExtended
from ..sources import list_alerts, list_alert_areas

router = APIRouter()


@router.get(
    '/alerts/areas',
    tags=['alerts'],
    name='List weather alert areas',
    response_description='List of weather alert areas for a country',
    response_model=list[AlertAreaWithPolygon],
    **defaults,
)
async def areas_list(country: CountryID) -> list[AlertAreaWithPolygon]:
    """List weather alert areas for a country."""
    return list_alert_areas(country)


@router.get(
    '/alerts/list',
    tags=['alerts'],
    name='List weather alerts',
    response_description='List of weather alerts for a country',
    response_model=list[AlertInfoExtended],
    **defaults,
)
async def alerts_list(
    country: CountryID, language: LanguageID = LanguageID.English
) -> list[AlertInfoExtended]:
    """List weather alerts for a country."""
    return await list_alerts(country, language)
