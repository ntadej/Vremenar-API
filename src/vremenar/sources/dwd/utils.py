"""DWD weather utils."""
from datetime import datetime
from typing import Any, Optional

from ...database.redis import redis
from ...database.stations import get_stations
from ...definitions import CountryID, ObservationType
from ...models.stations import StationBase, StationInfo, StationInfoExtended
from ...models.weather import WeatherCondition
from ...units import kelvin_to_celsius
from ...utils import chunker, day_or_night, parse_timestamp


async def get_mosmix_ids_for_timestamp(timestamp: str) -> set[str]:
    """Get MOSMIX IDs for timestamp from redis."""
    ids: set[str] = await redis.smembers(f'mosmix:{timestamp}')
    return ids


async def get_mosmix_records(ids: set[str]) -> list[dict[str, Any]]:
    """Get MOSMIX records from redis."""
    result: list[dict[str, Any]] = []

    async with redis.client() as connection:
        for batch in chunker(list(ids), 100):
            async with connection.pipeline(transaction=False) as pipeline:
                for id in batch:
                    pipeline.hgetall(id)
                response = await pipeline.execute()
            result.extend(response)

    return result


def get_icon_base(weather: dict[str, Any]) -> str:
    """Get base icon from weather data."""
    weather_condition = weather.get('condition', None)
    if weather_condition == 'fog':
        return 'FG'

    cloud_cover = float(weather.get('cloud_cover', 0))
    cloud_cover_fraction = cloud_cover / 100
    if cloud_cover_fraction < 1 / 8:
        return 'clear'
    elif 1 / 8 <= cloud_cover_fraction < 4 / 8:
        return 'partCloudy'
    elif 4 / 8 <= cloud_cover_fraction < 7 / 8:
        return 'prevCloudy'
    return 'overcast'


def get_icon_condition(weather: dict[str, Any]) -> Optional[str]:
    """Get icon condition from weather data."""
    weather_condition = weather.get('condition', None)

    precipitation_intensity = float(
        weather.get('precipitation_60', weather.get('precipitation', 0))
    )
    if precipitation_intensity <= 0 or weather_condition == 'dry':
        return None

    if precipitation_intensity > 10:
        intensity = 'heavy'
    elif precipitation_intensity > 2.5:
        intensity = 'mod'
    else:
        intensity = 'light'

    if weather_condition in ['hail', 'sleet']:
        precipitation_type = 'SHGR'
    elif weather_condition == 'thunderstorm':
        precipitation_type = 'TSRA'
    elif weather_condition == 'snow':
        precipitation_type = 'SN'
    else:
        precipitation_type = 'RA'

    return f'{intensity}{precipitation_type}'


def get_icon(weather: dict[str, Any], station: StationInfo, time: datetime) -> str:
    """Get icon from weather data."""
    # SOURCE:
    # conditions: dry, fog, rain, sleet, snow, hail, thunderstorm, null
    #
    # ICONS:
    # time: day/night
    # base: FG, clear, overcast, partCloudy, prevCloudy
    # intensity: light, mod, heavy
    # modifiers: DZ (drizzle), FG (fog), RA (rain), RASN (rain+snow), SN (snow),
    #            SHGR (hail shower), SHRA (rain shower),
    #            SHRASN (rain+snow shower), SHSN (snow shower),
    #            TS (thunderstorm), TSGR(hail thunderstorm), TSRA (rain thunderstorm),
    #            TSRASN(rain+snow thunderstorm), TSSN (snow thunderstorm)
    #
    # CRITERIA:
    # rain:
    #   light - when the precipitation rate is < 2.5 mm per hour
    #   moderate - when the precipitation rate is between 2.5 mm and 10 mm per hour
    #   heavy - when the precipitation rate is > 10 mm per hour
    # sky:
    #   clear - 0 to 1/8
    #   partly cloudy - 1/8 to 4/8
    #   mostly cloudy - 4/8 to 7/8
    #   overcast - 7/8 to 1

    time_of_day = day_or_night(station.coordinate, time)
    base_icon = get_icon_base(weather)
    condition = get_icon_condition(weather)
    if condition:
        return f'{base_icon}_{condition}_{time_of_day}'
    return f'{base_icon}_{time_of_day}'


async def parse_record(
    record: dict[str, Any], observation: ObservationType
) -> tuple[Optional[StationBase], Optional[WeatherCondition]]:
    """Parse DWD record."""
    station_id = record['station_id']
    stations = await get_stations(CountryID.Germany)

    if station_id not in stations:  # pragma: no cover
        return None, None

    station: Optional[StationInfoExtended] = stations.get(station_id, None)
    if not station:  # pragma: no cover
        return None, None

    if not station.metadata or station.metadata['status'] != '1':  # pragma: no cover
        return None, None

    condition = WeatherCondition(
        observation=observation,
        timestamp=record['timestamp'],
        icon=get_icon(record, station, parse_timestamp(record['timestamp'])),
        temperature=kelvin_to_celsius(float(record['temperature'])),
    )

    return station, condition


async def parse_source(source: dict[str, Any]) -> Optional[StationInfoExtended]:
    """Parse DWD weather source."""
    stations = await get_stations(CountryID.Germany)
    source_id = source['wmo_station_id']
    return stations.get(source_id, None)
