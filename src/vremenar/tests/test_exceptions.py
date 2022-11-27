"""Exceptions tests."""
from pytest import raises

from ..exceptions import (
    UnsupportedCountryException,
    UnsupportedMapTypeException,
    UnrecognisedMapIDException,
    UnknownAlertAreaException,
    UnknownStationAlertAreaException,
    UnknownStationException,
    InvalidSearchQueryException,
)


def test_exceptions() -> None:
    """Test exceptions."""
    with raises(UnsupportedCountryException):
        raise UnsupportedCountryException()

    with raises(UnsupportedMapTypeException):
        raise UnsupportedMapTypeException()

    with raises(UnrecognisedMapIDException):
        raise UnrecognisedMapIDException()

    with raises(UnknownAlertAreaException):
        raise UnknownAlertAreaException()

    with raises(UnknownStationAlertAreaException):
        raise UnknownStationAlertAreaException()

    with raises(UnknownStationException):
        raise UnknownStationException()

    with raises(InvalidSearchQueryException):
        raise InvalidSearchQueryException("Test message")
