"""Version API tests."""

from fastapi.testclient import TestClient

from vremenar.main import app

client = TestClient(app)


def test_version() -> None:
    """Test version."""
    response = client.get("/version")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    assert response.headers["CDN-Cache-Control"] == "public, max-age=3600"
