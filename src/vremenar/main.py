"""Vremenar backend main application."""

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from .api import version
from .api import stations
from .api import maps

app = FastAPI()
app.add_middleware(GZipMiddleware)
app.include_router(version)
app.include_router(stations)
app.include_router(maps)
