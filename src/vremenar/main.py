"""Vremenar backend main application."""

from fastapi import FastAPI
from fastapi.middleware.gzip import GZipMiddleware

from . import __version__
from .api import version, stations, maps, copyright

tags_metadata = [
    {
        'name': 'version',
        'description': 'Vremenar version infromation used for update notifications.',
    },
    {
        'name': 'stations',
        'description': 'Weather stations information and maps,'
        'including weather information.',
    },
    {
        'name': 'maps',
        'description': 'Query available weather maps and their information.',
    },
    {
        'name': 'copyright',
        'description': 'Data attribution and copyright.',
    },
]

app: FastAPI = FastAPI(
    title='Vremenar API',
    description='Weather API powering Vremenar application',
    version=__version__,
    openapi_tags=tags_metadata,
)
app.add_middleware(GZipMiddleware)
app.include_router(version)
app.include_router(stations)
app.include_router(maps)
app.include_router(copyright)

__all__ = ['app']
