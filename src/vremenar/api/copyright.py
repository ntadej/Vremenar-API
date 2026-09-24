"""Copyright API."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel, ConfigDict

from vremenar.definitions import CountryID
from vremenar.sources.arso import ARSO_NAME, ARSO_URL
from vremenar.sources.dwd import DWD_NAME, DWD_URL
from vremenar.sources.librewxr import LIBREWXR_NAME, LIBREWXR_URL

from .cache import CACHE_HOUR, cache_dependency

router = APIRouter()


class CopyrightInfo(BaseModel):
    """Copyright info."""

    provider: str
    url: str

    model_config = ConfigDict(
        title="Copyright info",
        json_schema_extra={
            "examples": [
                {
                    "provider": ARSO_NAME,
                    "url": ARSO_URL,
                },
            ],
        },
    )


@router.get(
    "/copyright",
    tags=["copyright"],
    response_description="Get data copyright",
    dependencies=[Depends(cache_dependency(CACHE_HOUR))],
)
async def copyright() -> dict[str, list[CopyrightInfo]]:  # ruff: ignore[builtin-variable-shadowing]
    """Get data copyright."""
    return {
        CountryID.Slovenia: [
            CopyrightInfo(provider=ARSO_NAME, url=ARSO_URL),
            CopyrightInfo(provider=LIBREWXR_NAME, url=LIBREWXR_URL),
        ],
        CountryID.Germany: [
            CopyrightInfo(provider=DWD_NAME, url=DWD_URL),
            CopyrightInfo(provider=LIBREWXR_NAME, url=LIBREWXR_URL),
        ],
        CountryID.Global: [
            CopyrightInfo(provider=LIBREWXR_NAME, url=LIBREWXR_URL),
        ],
    }
