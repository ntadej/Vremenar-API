"""Vremenar backend main application."""

from fastapi import FastAPI

from . import __version__
from .api import version, stations, maps, alerts, copyright
from .database import database_info

# Should not be enabled in production!
debug = False

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

if debug:
    from fastapi_profiler.profiler_middleware import (  # type: ignore
        PyInstrumentProfilerMiddleware,
    )

    app.add_middleware(PyInstrumentProfilerMiddleware)

database_info()

__all__ = ["app"]
