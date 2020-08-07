"""Vremenar backend main application."""

from fastapi import FastAPI

from .api import maps
from .api import weather_map

app = FastAPI()
app.include_router(maps)
app.include_router(weather_map)
