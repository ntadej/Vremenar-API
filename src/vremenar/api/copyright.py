"""Copyright API."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from vremenar.definitions import CountryID
from vremenar.sources.arso import ARSO_NAME, ARSO_URL
from vremenar.sources.dwd import DWD_NAME, DWD_URL
from vremenar.sources.rainviewer import RAINVIEWER_NAME, RAINVIEWER_URL

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
)
async def copyright() -> dict[str, list[CopyrightInfo]]:  # noqa: A001
    """Get data copyright."""
    return {
        CountryID.Slovenia: [
            CopyrightInfo(provider=ARSO_NAME, url=ARSO_URL),
            CopyrightInfo(provider=RAINVIEWER_NAME, url=RAINVIEWER_URL),
        ],
        CountryID.Germany: [
            CopyrightInfo(provider=DWD_NAME, url=DWD_URL),
            CopyrightInfo(provider=RAINVIEWER_NAME, url=RAINVIEWER_URL),
        ],
        CountryID.Global: [
            CopyrightInfo(provider=RAINVIEWER_NAME, url=RAINVIEWER_URL),
        ],
    }
