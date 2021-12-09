"""Stations API tests."""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient

from vremenar.main import app

client = TestClient(app)


def test_stations_list() -> None:
    """Test stations list."""
    response = client.get('/stations/list?country=si')
    assert response.status_code == 200

    response = client.get('/stations/list?country=de')
    assert response.status_code == 200


def test_stations_details() -> None:
    """Test stations details."""
    response = client.get('/stations/list?country=si&extended=true')
    assert response.status_code == 200

    response = client.get('/stations/list?country=de&extended=true')
    assert response.status_code == 200


def test_stations_find_string() -> None:
    """Test stations find by string."""
    response = client.post('/stations/find?country=si', json={'string': 'Bled'})
    assert response.status_code == 200

    response = client.post('/stations/find?country=de', json={'string': 'Hamburg'})
    assert response.status_code == 422
    assert response.json()['detail'] == 'Only coordinates are required'


def test_stations_find_coordinate() -> None:
    """Test stations find by coordinate."""
    response = client.post(
        '/stations/find?country=si',
        json={
            'latitude': 46.3684,
            'longitude': 14.1101,
        },
    )
    assert response.status_code == 200

    response = client.post(
        '/stations/find?country=de',
        json={
            'latitude': 53.5511,
            'longitude': 9.9937,
        },
    )
    assert response.status_code == 200


def test_stations_find_errors() -> None:
    """Test stations find errors."""
    response = client.get('/stations/find?country=si')
    assert response.status_code == 405
    assert response.json()['detail'] == 'Method Not Allowed'

    response = client.post('/stations/find?country=si')
    assert response.status_code == 422
    assert response.json()['detail'][0]['type'] == 'value_error.missing'
    assert response.json()['detail'][0]['loc'] == ['body']

    response = client.post(
        '/stations/find?country=si',
        json={
            'string': 'Bled',
            'latitude': 46.3684,
            'longitude': 14.1101,
        },
    )
    assert response.status_code == 422
    assert (
        response.json()['detail'] == 'Either search string or coordinates are required'
    )


def test_stations_condition() -> None:
    """Test stations condition."""
    response = client.get('/stations/condition/METEO-0038?country=si')
    assert response.status_code == 200

    response = client.get('/stations/condition/10147?country=de')
    assert response.status_code == 200


def test_stations_condition_error() -> None:
    """Test stations condition errors."""
    response = client.get('/stations/condition?country=si')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Not Found'

    response = client.get('/stations/condition/METEO-12345?country=si')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Unknown station'

    response = client.get('/stations/condition/12345?country=de')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Unknown station'


def test_stations_map() -> None:
    """Test stations map."""
    response = client.get('/stations/map/current?country=si')
    assert response.status_code == 200

    response = client.get('/stations/map/d2h00?country=si')
    assert response.status_code == 200

    response = client.get('/stations/map/d7?country=si')
    assert response.status_code == 200

    response = client.get('/stations/map/current?country=de')
    assert response.status_code == 200

    now = datetime.now(tz=timezone.utc)
    now = now.replace(minute=0, second=0, microsecond=0)
    soon = now + timedelta(hours=1)
    soon_string = soon.strftime('%Y-%m-%dT%H:%M:%SZ')
    response = client.get(f'/stations/map/{soon_string}?country=de')
    assert response.status_code == 200


def test_stations_errors() -> None:
    """Test stations map errors."""
    response = client.get('/stations/map/abc?country=si')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Map ID is not recognised'

    response = client.get('/stations/map/dabc?country=si')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Map ID is not recognised'

    response = client.get('/stations/map/abc?country=de')
    assert response.status_code == 404
    assert response.json()['detail'] == 'Map ID is not recognised'
