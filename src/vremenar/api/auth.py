"""API key authentication."""

from os import getenv
from secrets import compare_digest
from typing import Annotated

from fastapi import Request, Security
from fastapi.security import APIKeyHeader

from vremenar.exceptions import InvalidAPIKeyException

api_key: str = getenv("VREMENAR_API_KEY", "")


class RawAPIKeyHeader(APIKeyHeader):
    """API key header that tells an empty header apart from a missing one."""

    async def __call__(self, request: Request) -> str | None:
        """Return the raw header value, or `None` if the header is absent."""
        return request.headers.get(self.model.name)


api_key_header = RawAPIKeyHeader(
    name="X-API-Key",
    scheme_name="APIKeyHeader",
    auto_error=False,
    description="API key. Optional, but must be valid if provided.",
)


def validate_api_key(
    key: Annotated[str | None, Security(api_key_header)],
) -> None:
    """Validate the API key, if one is configured and provided."""
    if not api_key:  # authentication is disabled
        return

    if key is None:  # the key is optional, an empty one is not
        return

    if not compare_digest(key.encode(), api_key.encode()):
        raise InvalidAPIKeyException
