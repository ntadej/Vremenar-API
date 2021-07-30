"""Copyright API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field
from typing import Dict

from ..definitions import CountryID

router = APIRouter()


class CopyrightInfo(BaseModel):
    """Copyright info."""

    provider: str = Field(..., example='Slovenian Environment Agency')
    url: str = Field(..., example='https://meteo.arso.gov.si')


@router.get(
    '/copyright',
    tags=['copyright'],
    response_description='Get data copyright',
    response_model=Dict[CountryID, CopyrightInfo],
)
async def copyright() -> Dict[CountryID, CopyrightInfo]:
    """Get data copyright."""
    return {
        CountryID.Slovenia: CopyrightInfo(
            provider='Slovenian Environment Agency', url='https://meteo.arso.gov.si'
        ),
        CountryID.Germany: CopyrightInfo(
            provider='Deutscher Wetterdienst', url='https://dwd.de'
        ),
    }
