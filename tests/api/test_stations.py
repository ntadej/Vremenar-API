"""Stations API tests."""
from datetime import datetime, timedelta, timezone

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio()
async def test_stations_list(client: AsyncClient) -> None:
    """Test stations list."""
    response = await client.get("/stations/list?country=si")
    assert response.status_code == 200

    response = await client.get("/stations/list?country=de")
    assert response.status_code == 200


@pytest.mark.asyncio()
async def test_stations_details(client: AsyncClient) -> None:
    """Test stations details."""
    response = await client.get("/stations/list?country=si")
    assert response.status_code == 200

    response = await client.get("/stations/list?country=de")
    assert response.status_code == 200

    response = await client.get("/stations/list?country=si&extended=true")
    assert response.status_code == 200

    response = await client.get("/stations/list?country=de&extended=true")
    assert response.status_code == 200


@pytest.mark.asyncio()
async def test_stations_find_string(client: AsyncClient) -> None:
    """Test stations find by string."""
    response = await client.post("/stations/find?country=si", json={"string": "Bled"})
    assert response.status_code == 200

    response = await client.post("/stations/find?country=si", json={"string": "Kranj"})
    assert response.status_code == 200

    response = await client.post(
        "/stations/find?country=de",
        json={"string": "Hamburg"},
    )
    assert response.status_code == 422
    assert response.json()["detail"] == "Only coordinates are required"


@pytest.mark.asyncio()
async def test_stations_find_coordinate(client: AsyncClient) -> None:
    """Test stations find by coordinate."""
    # Bled
    response = await client.post(
        "/stations/find?country=si",
        json={
            "latitude": 46.3684,
            "longitude": 14.1101,
        },
    )
    assert response.status_code == 200

    # Hamburg (simple)
    response = await client.post(
        "/stations/find?country=de",
        json={
            "latitude": 53.5511,
            "longitude": 9.9937,
        },
    )
    assert response.status_code == 200

    # invalid
    response = await client.post(
        "/stations/find?country=de&include_forecast_only=true",
        json={
            "latitude": 50.63,
            "longitude": 10,
        },
    )
    assert response.status_code == 200

    # Hamburg
    response = await client.post(
        "/stations/find?country=de&include_forecast_only=true",
        json={
            "latitude": 53.63,
            "longitude": 10,
        },
    )
    assert response.status_code == 200

    # Near Hamburg
    response = await client.post(
        "/stations/find?country=de&include_forecast_only=true",
        json={
            "latitude": 53.6022,
            "longitude": 9.8374,
        },
    )
    assert response.status_code == 200


@pytest.mark.asyncio()
async def test_stations_find_errors(client: AsyncClient) -> None:
    """Test stations find errors."""
    response = await client.get("/stations/find?country=si")
    assert response.status_code == 405
    assert response.json()["detail"] == "Method Not Allowed"

    response = await client.post("/stations/find?country=si")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error.missing"
    assert response.json()["detail"][0]["loc"] == ["body"]

    response = await client.post("/stations/find?country=si", json={})
    assert response.status_code == 422
    assert (
        response.json()["detail"] == "Either search string or coordinates are required"
    )

    response = await client.post("/stations/find?country=de", json={})
    assert response.status_code == 422
    assert response.json()["detail"] == "Only coordinates are required"

    response = await client.post(
        "/stations/find?country=si",
        json={
            "string": "Bled",
            "latitude": 46.3684,
            "longitude": 14.1101,
        },
    )
    assert response.status_code == 422
    assert (
        response.json()["detail"] == "Either search string or coordinates are required"
    )


@pytest.mark.asyncio()
async def test_stations_condition(client: AsyncClient) -> None:
    """Test stations condition."""
    response = await client.get("/stations/condition/METEO-0038?country=si")
    assert response.status_code == 200

    response = await client.get("/stations/condition/10147?country=de")
    assert response.status_code == 200

    response = await client.get(
        "/stations/condition/METEO-0038?country=si&extended=true",
    )
    assert response.status_code == 200

    response = await client.get("/stations/condition/10147?country=de&extended=true")
    assert response.status_code == 200


@pytest.mark.asyncio()
async def test_stations_condition_error(client: AsyncClient) -> None:
    """Test stations condition errors."""
    response = await client.get("/stations/condition?country=si")
    assert response.status_code == 404
    assert response.json()["detail"] == "Not Found"

    response = await client.get("/stations/condition/METEO-12345?country=si")
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown station"

    response = await client.get("/stations/condition/12345?country=de")
    assert response.status_code == 404
    assert response.json()["detail"] == "Unknown station"


@pytest.mark.asyncio()
async def test_stations_map(client: AsyncClient) -> None:
    """Test stations map."""
    response = await client.get("/stations/map/current?country=si&extended=false")
    assert response.status_code == 200

    response = await client.get("/stations/map/current?country=si&extended=true")
    assert response.status_code == 200

    response = await client.get("/stations/map/d2h00?country=si")
    assert response.status_code == 200

    response = await client.get("/stations/map/d7?country=si")
    assert response.status_code == 200

    response = await client.get("/stations/map/current?country=de&extended=false")
    assert response.status_code == 200

    response = await client.get("/stations/map/current?country=de&extended=true")
    assert response.status_code == 200

    now = datetime.now(tz=timezone.utc)
    now = now.replace(minute=0, second=0, microsecond=0)
    soon = now + timedelta(hours=1)
    soon_timestamp = f"{int(soon.timestamp())}000"
    response = await client.get(f"/stations/map/{soon_timestamp}?country=de")
    assert response.status_code == 200


@pytest.mark.asyncio()
async def test_stations_errors(client: AsyncClient) -> None:
    """Test stations map errors."""
    response = await client.get("/stations/map/abc?country=si")
    assert response.status_code == 404
    assert response.json()["detail"] == "Map ID is not recognised"

    response = await client.get("/stations/map/dabc?country=si")
    assert response.status_code == 404
    assert response.json()["detail"] == "Map ID is not recognised"

    response = await client.get("/stations/map/abc?country=de")
    assert response.status_code == 404
    assert response.json()["detail"] == "Map ID is not recognised"
