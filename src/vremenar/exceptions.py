"""Common Vremenar exceptions."""
from fastapi import HTTPException, status


class UnsupportedCountryException(HTTPException):
    """Unsupported country exception."""

    def __init__(self) -> None:
        """Init exception."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unsupported country",
        )


class UnsupportedMapTypeException(HTTPException):
    """Unsupported map type exception."""

    def __init__(self) -> None:
        """Init exception."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unsupported or unknown map type",
        )


class UnrecognisedMapIDException(HTTPException):
    """Unrecognised map ID exception."""

    def __init__(self) -> None:
        """Init exception."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Map ID is not recognised",
        )


class UnknownAlertAreaException(HTTPException):
    """Unknown alert area exception."""

    def __init__(self) -> None:
        """Init exception."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown alert area",
        )


class UnknownStationAlertAreaException(HTTPException):
    """Unknown station alert area exception."""

    def __init__(self) -> None:
        """Init exception."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Station has no assigned alerts area",
        )


class UnknownStationException(HTTPException):
    """Unknown station exception."""

    def __init__(self) -> None:
        """Init exception."""
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Unknown station",
        )


class InvalidSearchQueryException(HTTPException):
    """Invalid query exception."""

    def __init__(self, detail: str) -> None:
        """Init exception."""
        super().__init__(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=detail,
        )
