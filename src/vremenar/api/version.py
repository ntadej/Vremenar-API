"""App version API."""

from fastapi import APIRouter

router = APIRouter()


class VersionInfo:
    """Version info."""

    def __init__(self) -> None:
        """Initialize version info."""
        self.stable: str = ''
        self.beta: str = '0.2.0'


@router.get('/version', tags=['version'])
async def version() -> VersionInfo:
    """Get app version."""
    return VersionInfo()
