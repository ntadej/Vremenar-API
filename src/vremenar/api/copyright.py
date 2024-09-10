"""Copyright API."""

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from vremenar.definitions import CountryID

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
                    "provider": "Slovenian Environment Agency",
                    "url": "https://meteo.arso.gov.si",
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
        CountryID.Slovenia.value: [
            CopyrightInfo(
                provider="Slovenian Environment Agency",
                url="https://meteo.arso.gov.si",
            ),
            CopyrightInfo(
                provider="RainViewer",
                url="https://www.rainviewer.com",
            ),
        ],
        CountryID.Germany.value: [
            CopyrightInfo(
                provider="Deutscher Wetterdienst",
                url="https://dwd.de",
            ),
            CopyrightInfo(
                provider="RainViewer",
                url="https://www.rainviewer.com",
            ),
        ],
        CountryID.Global.value: [
            CopyrightInfo(
                provider="RainViewer",
                url="https://www.rainviewer.com",
            ),
        ],
    }
