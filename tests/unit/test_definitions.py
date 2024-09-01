"""Definitions tests."""

from vremenar.definitions import CountryID


def test_country_id() -> None:
    """Test CountryID."""
    slovenia = CountryID.Slovenia
    germany = CountryID.Germany
    global_country = CountryID.Global

    assert slovenia.label() == "Slovenia"
    assert slovenia.full_name() == "slovenia"

    assert germany.label() == "Germany"
    assert germany.full_name() == "germany"

    assert global_country.label() == "Global"
    assert global_country.full_name() == "global"
