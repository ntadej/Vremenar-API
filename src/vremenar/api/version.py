"""Version API."""

from json import load
from pathlib import Path
from typing import Dict, Optional

from fastapi import APIRouter
from pydantic import BaseModel, Field

from .. import __version__

router = APIRouter()
VERSION_INFO: Path = Path.cwd() / 'version.json'


class VersionInfo(BaseModel):
    """Version info."""

    stable: Optional[str] = Field('', example='1.0.0')
    beta: Optional[str] = Field('', example='2.0.0')
    server: str = Field(__version__, const=True, example='1.0.0')

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
    """Get app and server versions."""
    data: Dict[str, str] = {}

    if VERSION_INFO.is_file():
        with VERSION_INFO.open() as f:
            data = load(f)

    stable = data['stable'] if 'stable' in data else ''
    beta = data['beta'] if 'beta' in data else ''

    return VersionInfo(stable=stable, beta=beta)
