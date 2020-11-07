"""App version API."""

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class VersionInfo(BaseModel):
    """Version info."""

    stable: str = Field('', const=True, example='1.0.0')
    beta: str = Field('0.2.0', const=True, example='0.2.0')

    class Config:
        """Version info config."""

        title: str = 'Version info'


@router.get(
    '/version',
    tags=['version'],
    response_description='Get Vremenar versions',
    response_model=VersionInfo,
)
async def version() -> VersionInfo:
    """Get app version."""
    return VersionInfo()
