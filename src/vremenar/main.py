"""Vremenar backend main application."""

from fastapi import FastAPI

from .api import version
from .api import location
from .api import maps
from .api import weather_map

app = FastAPI()
app.include_router(version)
app.include_router(location)
app.include_router(maps)
app.include_router(weather_map)
