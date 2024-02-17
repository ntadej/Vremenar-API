"""Exceptions tests."""
import pytest

from vremenar.exceptions import (
    InvalidSearchQueryException,
    UnknownAlertAreaException,
    UnknownStationAlertAreaException,
    UnknownStationException,
    UnrecognisedMapIDException,
    UnsupportedCountryException,
    UnsupportedMapTypeException,
)


def test_exceptions() -> None:
    """Test exceptions."""
    with pytest.raises(UnsupportedCountryException):
        raise UnsupportedCountryException()

    with pytest.raises(UnsupportedMapTypeException):
        raise UnsupportedMapTypeException()

    with pytest.raises(UnrecognisedMapIDException):
        raise UnrecognisedMapIDException()

    with pytest.raises(UnknownAlertAreaException):
        raise UnknownAlertAreaException()

    with pytest.raises(UnknownStationAlertAreaException):
        raise UnknownStationAlertAreaException()

    with pytest.raises(UnknownStationException):
        raise UnknownStationException()

    err = "Test message"
    with pytest.raises(InvalidSearchQueryException):
        raise InvalidSearchQueryException(err)
