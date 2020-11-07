"""Vremenar backend main application."""

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from .api import version
from .api import stations
from .api import maps
from .api import weather_map

app = FastAPI()
app.add_middleware(GZipMiddleware)
app.include_router(version)
app.include_router(stations)
app.include_router(maps)
app.include_router(weather_map)
