"""ARSO weather stations."""
from vremenar.database.stations import get_stations, search_stations
from vremenar.definitions import CountryID, ObservationType
from vremenar.exceptions import InvalidSearchQueryException, UnknownStationException
from vremenar.models.stations import (
    StationInfo,
    StationInfoExtended,
    StationSearchModel,
)
from vremenar.models.weather import WeatherInfoExtended

from .utils import get_weather_records, parse_record


async def list_stations() -> list[StationInfoExtended]:
    """List ARSO weather stations."""
    stations = await get_stations(CountryID.Slovenia)
    return list(stations.values())


async def find_station(query: StationSearchModel) -> list[StationInfo]:
    """Find station by coordinate."""
    if query.latitude is None or query.longitude is None:
        err = "Coordinates are required"
        raise InvalidSearchQueryException(err)

    stations = await search_stations(
        CountryID.Slovenia,
        query.latitude,
        query.longitude,
    )

    return [station.info() for station in stations][:5]


async def current_station_condition(station_id: str) -> WeatherInfoExtended:
    """Get current station weather condition."""
    stations = await get_stations(CountryID.Slovenia)
    station: StationInfoExtended | None = stations.get(station_id, None)
    if not station:
        raise UnknownStationException()

    records = await get_weather_records({f"arso:weather:current:{station_id}"})

    for record in records:
        if not record:  # pragma: no cover
            continue

        _, condition = await parse_record(record, ObservationType.Recent)
        if condition:
            return WeatherInfoExtended(station=station, condition=condition)

    raise UnknownStationException()  # pragma: no cover
