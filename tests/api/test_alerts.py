"""Alerts API tests."""
import pytest

from httpx import AsyncClient


@pytest.mark.asyncio
async def test_alerts_areas(client: AsyncClient) -> None:
    """Test alerts areas."""
    response = await client.get("/alerts/areas?country=si")
    assert response.status_code == 200

    response = await client.get("/alerts/areas?country=de")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_alerts_full_list(client: AsyncClient) -> None:
    """Test alerts full list."""
    response = await client.get("/alerts/full_list?country=si")
    assert response.status_code == 200

    response = await client.get("/alerts/full_list?country=de")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_alerts_list(client: AsyncClient) -> None:
    """Test alerts list."""
    response = await client.get("/alerts/list?country=si")
    assert response.status_code == 422

    response = await client.get("/alerts/list?country=de")
    assert response.status_code == 422

    response = await client.get("/alerts/list?country=de&station=FOO")
    assert response.status_code == 404

    response = await client.get("/alerts/list?country=de&station=10147")
    assert response.status_code == 200

    response = await client.get("/alerts/list?country=de&station=10147&station=P0201")
    assert response.status_code == 200

    response = await client.get("/alerts/list?country=de&area=FOO")
    assert response.status_code == 404

    response = await client.get("/alerts/list?country=de&area=DE048")
    assert response.status_code == 200

    response = await client.get("/alerts/list?country=de&area=DE048&area=DE413")
    assert response.status_code == 200

    response = await client.get(
        "/alerts/list?country=de&area=DE048&area=DE413&station=10147&station=P0201"
    )
    assert response.status_code == 200
