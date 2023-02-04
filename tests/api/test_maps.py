"""Maps API tests."""

from fastapi.testclient import TestClient
from vremenar.main import app

client = TestClient(app)


def test_maps_types() -> None:
    """Test maps types."""
    response = client.get("/maps/types?country=si")
    assert response.status_code == 200

    response = client.get("/maps/types?country=de")
    assert response.status_code == 200


def test_maps_list_condition() -> None:
    """Test maps list - condition."""
    response = client.get("/maps/list/condition?country=si")
    assert response.status_code == 200

    response = client.get("/maps/list/condition?country=de")
    assert response.status_code == 200


def test_maps_list_precipitation() -> None:
    """Test maps list - precipitation."""
    response = client.get("/maps/list/precipitation?country=si")
    assert response.status_code == 200

    response = client.get("/maps/list/precipitation?country=de")
    assert response.status_code == 200


def test_maps_list_cloud() -> None:
    """Test maps list - cloud."""
    response = client.get("/maps/list/cloud?country=si")
    assert response.status_code == 200

    response = client.get("/maps/list/cloud?country=de")
    assert response.status_code == 404


def test_maps_list_wind() -> None:
    """Test maps list - wind."""
    response = client.get("/maps/list/wind?country=si")
    assert response.status_code == 200

    response = client.get("/maps/list/wind?country=de")
    assert response.status_code == 404


def test_maps_list_temperature() -> None:
    """Test maps list - temperature."""
    response = client.get("/maps/list/temperature?country=si")
    assert response.status_code == 200

    response = client.get("/maps/list/temperature?country=de")
    assert response.status_code == 200


def test_maps_list_hail() -> None:
    """Test maps list - hail."""
    response = client.get("/maps/list/hail?country=si")
    assert response.status_code == 200

    response = client.get("/maps/list/hail?country=de")
    assert response.status_code == 404


def test_maps_list_uv_index_max() -> None:
    """Test maps list - hail."""
    response = client.get("/maps/list/uv_index_max?country=si")
    assert response.status_code == 404

    response = client.get("/maps/list/uv_index_max?country=de")
    assert response.status_code == 200


def test_maps_list_uv_dose() -> None:
    """Test maps list - hail."""
    response = client.get("/maps/list/uv_dose?country=si")
    assert response.status_code == 404

    response = client.get("/maps/list/uv_dose?country=de")
    assert response.status_code == 200


def test_maps_blank() -> None:
    """Test blank map type."""
    response = client.get("/maps/list")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}

    response = client.get("/maps/list/")
    assert response.status_code == 404
    assert response.json() == {"detail": "Not Found"}


def test_maps_invalid() -> None:
    """Test maps invalid map type."""
    response = client.get("/maps/list/invalid?country=si")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "type_error.enum"
    assert response.json()["detail"][0]["loc"] == ["path", "map_type"]


def test_maps_no_country() -> None:
    """Test maps list without country."""
    response = client.get("/maps/list/condition")
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "value_error.missing"
    assert response.json()["detail"][0]["loc"] == ["query", "country"]


def test_maps_all_legends() -> None:
    """Test maps legends - all."""
    response = client.get("/maps/legend?country=si")
    assert response.status_code == 200

    response = client.get("/maps/legend?country=de")
    assert response.status_code == 200


def test_maps_legends() -> None:
    """Test maps legends."""
    response = client.get("/maps/legend/condition?country=si")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unsupported or unknown map type"}

    response = client.get("/maps/legend/precipitation?country=si")
    assert response.status_code == 200

    response = client.get("/maps/legend/precipitation?country=de")
    assert response.status_code == 200

    response = client.get("/maps/legend/wind?country=si")
    assert response.status_code == 200

    response = client.get("/maps/legend/wind?country=de")
    assert response.status_code == 404
    assert response.json() == {"detail": "Unsupported or unknown map type"}

    response = client.get("/maps/legend/temperature?country=si")
    assert response.status_code == 200

    response = client.get("/maps/legend/hail?country=si")
    assert response.status_code == 200
