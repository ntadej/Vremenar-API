"""Maps API tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from httpx import AsyncClient


@pytest.mark.asyncio
async def test_maps_types(client: AsyncClient) -> None:
    """Test maps types."""
    response = await client.get("/maps/types?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/types?country=de")
    assert response.status_code == 200

    response = await client.get("/maps/types?country=global")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_maps_list_condition(client: AsyncClient) -> None:
    """Test maps list - condition."""
    response = await client.get("/maps/list/condition?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/list/condition?country=de")
    assert response.status_code == 200

    response = await client.get("/maps/list/condition?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_list_precipitation(client: AsyncClient) -> None:
    """Test maps list - precipitation."""
    response = await client.get("/maps/list/precipitation?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/list/precipitation?country=de")
    assert response.status_code == 200

    response = await client.get("/maps/list/precipitation?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_list_precipitation_global(client: AsyncClient) -> None:
    """Test maps list - precipitation."""
    response = await client.get("/maps/list/precipitation_global?country=si")
    assert response.status_code == 404

    response = await client.get("/maps/list/precipitation_global?country=de")
    assert response.status_code == 404

    response = await client.get("/maps/list/precipitation_global?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_list_cloud(client: AsyncClient) -> None:
    """Test maps list - cloud."""
    response = await client.get("/maps/list/cloud?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/list/cloud?country=de")
    assert response.status_code == 404

    response = await client.get("/maps/list/cloud?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_list_wind(client: AsyncClient) -> None:
    """Test maps list - wind."""
    response = await client.get("/maps/list/wind?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/list/wind?country=de")
    assert response.status_code == 404

    response = await client.get("/maps/list/wind?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_list_temperature(client: AsyncClient) -> None:
    """Test maps list - temperature."""
    response = await client.get("/maps/list/temperature?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/list/temperature?country=de")
    assert response.status_code == 200

    response = await client.get("/maps/list/temperature?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_list_hail(client: AsyncClient) -> None:
    """Test maps list - hail."""
    response = await client.get("/maps/list/hail?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/list/hail?country=de")
    assert response.status_code == 404

    response = await client.get("/maps/list/hail?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_list_uv_index_max(client: AsyncClient) -> None:
    """Test maps list - hail."""
    response = await client.get("/maps/list/uv_index_max?country=si")
    assert response.status_code == 404

    response = await client.get("/maps/list/uv_index_max?country=de")
    assert response.status_code == 200

    response = await client.get("/maps/list/uv_index_max?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_list_uv_dose(client: AsyncClient) -> None:
    """Test maps list - hail."""
    response = await client.get("/maps/list/uv_dose?country=si")
    assert response.status_code == 404

    response = await client.get("/maps/list/uv_dose?country=de")
    assert response.status_code == 200

    response = await client.get("/maps/list/uv_dose?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_blank(client: AsyncClient) -> None:
    """Test blank map type."""
    response = await client.get("/maps/list")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

    response = await client.get("/maps/list/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


@pytest.mark.asyncio
async def test_maps_invalid(client: AsyncClient) -> None:
    """Test maps invalid map type."""
    response = await client.get("/maps/list/invalid?country=si")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "enum"
    assert response.json()["detail"][0]["loc"] == ["path", "map_type"]


@pytest.mark.asyncio
async def test_maps_no_country(client: AsyncClient) -> None:
    """Test maps list without country."""
    response = await client.get("/maps/list/condition")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "missing"
    assert response.json()["detail"][0]["loc"] == ["query", "country"]


@pytest.mark.asyncio
async def test_maps_all_legends(client: AsyncClient) -> None:
    """Test maps legends - all."""
    response = await client.get("/maps/legend?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/legend?country=de")
    assert response.status_code == 200

    response = await client.get("/maps/legend?country=global")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_maps_legends(client: AsyncClient) -> None:
    """Test maps legends."""
    response = await client.get("/maps/legend/condition?country=si")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unsupported or unknown map type"}

    response = await client.get("/maps/legend/precipitation?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/legend/precipitation?country=de")
    assert response.status_code == 200

    response = await client.get("/maps/legend/precipitation_global?country=si")
    assert response.status_code == 404

    response = await client.get("/maps/legend/precipitation_global?country=de")
    assert response.status_code == 404

    response = await client.get("/maps/legend/precipitation_global?country=global")
    assert response.status_code == 404

    response = await client.get("/maps/legend/wind?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/legend/wind?country=de")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unsupported or unknown map type"}

    response = await client.get("/maps/legend/temperature?country=si")
    assert response.status_code == 200

    response = await client.get("/maps/legend/hail?country=si")
    assert response.status_code == 200
