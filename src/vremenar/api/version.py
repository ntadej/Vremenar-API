"""Version API."""

from json import load
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from vremenar import __version__

router = APIRouter()
VERSION_INFO: Path = Path.cwd() / "version.json"


class VersionInfo(BaseModel):
    """Version info."""

    stable: str = ""
    beta: str = ""
    server: str = __version__

    model_config = ConfigDict(
        title="Version info",
        json_schema_extra={
            "examples": [
                {
                    "stable": "1.0.0",
                    "beta": "2.0.0",
                    "server": "1.0.0",
                },
            ],
        },
    )


@router.get(
    "/version",
    tags=["version"],
    response_description="Get Vremenar versions",
)
async def version() -> VersionInfo:
    """Get app and server versions."""
    data: dict[str, str] = {}

    if VERSION_INFO.is_file():  # pragma: no cover
        with VERSION_INFO.open() as f:
            data = load(f)

    stable = data.get("stable", "")
    beta = data.get("beta", "")

    return VersionInfo(stable=stable, beta=beta)
