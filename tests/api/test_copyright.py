"""Copyright API tests."""

from __future__ import annotations

from fastapi.testclient import TestClient

from vremenar.main import app

client = TestClient(app)


def test_copyright() -> None:
    """Test copyright."""
    response = client.get("/copyright")
    assert response.status_code == 200
    assert response.headers["Cache-Control"] == "public, max-age=3600"
    assert response.headers["CDN-Cache-Control"] == "public, max-age=3600"
