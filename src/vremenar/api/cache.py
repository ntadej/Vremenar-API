"""API response caching."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi import Response  # ruff: ignore[typing-only-third-party-import]

if TYPE_CHECKING:
    from collections.abc import Callable

CACHE_HOUR: int = 3600
CACHE_1MIN: int = 60
CACHE_5MIN: int = 300
CACHE_15MIN: int = 900


def set_cache_headers(
    response: Response,
    max_age: int,
    cdn_max_age: int | None = None,
) -> None:
    """Set cache headers for the response."""
    response.headers["Cache-Control"] = f"public, max-age={max_age}"
    response.headers["CDN-Cache-Control"] = (
        f"public, max-age={cdn_max_age if cdn_max_age is not None else max_age}"
    )


def cache_dependency(
    max_age: int,
    cdn_max_age: int | None = None,
) -> Callable[[Response], None]:
    """Make a dependency that caches the response for a fixed amount of time."""

    def set_cache_headers_fixed(response: Response) -> None:
        set_cache_headers(response, max_age, cdn_max_age)

    return set_cache_headers_fixed
