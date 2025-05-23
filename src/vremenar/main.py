"""Vremenar backend main application."""

from __future__ import annotations

from fastapi import FastAPI

from . import __version__
from .api import alerts, copyright, maps, stations, version  # noqa: A004
from .database import database_info

tags_metadata = [
    {
        "name": "version",
        "description": "Vremenar version infromation used for update notifications.",
    },
    {
        "name": "stations",
        "description": "Weather stations information and maps,"
        "including weather information.",
    },
    {
        "name": "maps",
        "description": "Query available weather maps and their information.",
    },
    {"name": "alerts", "description": "Weather alerts."},
    {
        "name": "copyright",
        "description": "Data attribution and copyright.",
    },
]

app: FastAPI = FastAPI(
    title="Vremenar API",
    description="Weather API powering Vremenar application",
    version=__version__,
    openapi_tags=tags_metadata,
)
app.include_router(version)
app.include_router(stations)
app.include_router(maps)
app.include_router(alerts)
app.include_router(copyright)

database_info()

__all__ = ["app"]
