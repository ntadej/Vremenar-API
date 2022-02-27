"""DWD weather utils."""
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from ...database.stations import get_stations
from ...definitions import CountryID, ObservationType
from ...models.stations import StationBase, StationInfo, StationInfoExtended
from ...models.weather import WeatherCondition
from ...units import kelvin_to_celsius
from ...utils import day_or_night, parse_time, parse_timestamp

CACHE_PATH: Path = Path.cwd() / '.cache/dwd'


def get_icon(station: StationInfo, weather: dict[str, Any], time: datetime) -> str:
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
    #   partly cloudy - 1/8 to
    #   mostly cloudy -
    #   overcast -

    time_of_day = day_or_night(station.coordinate, time)
    base_icon = 'clear'
    condition = None
    if weather['condition'] == 'fog':  # TODO: intensity
        base_icon = 'FG'
    elif 'cloud_cover' in weather and weather['cloud_cover'] is not None:
        cloud_cover_fraction = weather['cloud_cover'] / 100
        if 1 / 8 <= cloud_cover_fraction < 4 / 8:
            base_icon = 'partCloudy'
        elif 4 / 8 <= cloud_cover_fraction < 7 / 8:
            base_icon = 'prevCloudy'
        else:
            base_icon = 'overcast'

    precipitation_intensity = (
        weather['precipitation_60']
        if 'precipitation_60' in weather
        else weather['precipitation']
    )
    if precipitation_intensity > 0:  # TODO: snow intensity
        if precipitation_intensity > 10:
            intensity = 'heavy'
        elif precipitation_intensity > 2.5:
            intensity = 'mod'
        else:
            intensity = 'light'

        if weather['condition'] in ['hail', 'sleet']:
            precipitation_type = 'SHGR'
        elif weather['condition'] == 'thunderstorm':
            precipitation_type = 'TSRA'
        elif weather['condition'] == 'snow':
            precipitation_type = 'SN'
        else:
            precipitation_type = 'RA'

        condition = f'{intensity}{precipitation_type}'

    if condition:
        return f'{base_icon}_{condition}_{time_of_day}'

    return f'{base_icon}_{time_of_day}'


def weather_map_url(map_id: str) -> Optional[Path]:
    """Generate forecast map URL."""
    paths = sorted(list(CACHE_PATH.glob('MOSMIX*.json')))
    now = datetime.utcnow()
    now = now.replace(tzinfo=timezone.utc)
    for path in paths:
        if map_id == 'current':
            name = path.name.replace('MOSMIX:', '').strip('.json')
            date = parse_time(name)
            delta = (date - now).total_seconds()

            if delta < 0:
                continue

            return path

        if path.name == f'MOSMIX:{map_id}.json':
            return path
    return None


async def parse_record(
    record: dict[str, Any], observation: ObservationType
) -> tuple[Optional[StationBase], Optional[WeatherCondition]]:
    """Parse DWD record."""
    station_id = record['wmo_station_id']
    stations = await get_stations(CountryID.Germany)

    if station_id not in stations:  # pragma: no cover
        return None, None

    station: Optional[StationInfoExtended] = stations.get(station_id, None)
    if not station:  # pragma: no cover
        return None, None

    if not station.metadata or station.metadata['status'] != '1':
        return None, None

    condition = WeatherCondition(
        observation=observation,
        timestamp=record['timestamp'],
        icon=get_icon(station, record, parse_timestamp(record['timestamp'])),
        temperature=kelvin_to_celsius(record['temperature']),
    )

    return station, condition


async def parse_source(source: dict[str, Any]) -> Optional[StationInfoExtended]:
    """Parse DWD weather source."""
    stations = await get_stations(CountryID.Germany)
    source_id = source['wmo_station_id']
    return stations.get(source_id, None)
