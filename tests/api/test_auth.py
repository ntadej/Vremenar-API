"""API key authentication tests."""

from __future__ import annotations

from typing import TYPE_CHECKING

from fastapi.testclient import TestClient

from vremenar.main import app

if TYPE_CHECKING:
    import pytest

client = TestClient(app)


def test_no_api_key_configured() -> None:
    """Test that requests pass through when no API key is configured."""
    response = client.get("/version")
    assert response.status_code == 200


def test_api_key_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a missing API key is accepted even when one is configured."""
    monkeypatch.setattr("vremenar.api.auth.api_key", "secret")
    response = client.get("/version")
    assert response.status_code == 200


def test_api_key_invalid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an invalid API key is rejected when one is provided."""
    monkeypatch.setattr("vremenar.api.auth.api_key", "secret")
    response = client.get("/version", headers={"X-API-Key": "invalid"})
    assert response.status_code == 401


def test_api_key_empty(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that an empty API key header is rejected."""
    monkeypatch.setattr("vremenar.api.auth.api_key", "secret")
    response = client.get("/version", headers={"X-API-Key": ""})
    assert response.status_code == 401


def test_api_key_valid(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that a valid API key is accepted."""
    monkeypatch.setattr("vremenar.api.auth.api_key", "secret")
    response = client.get("/version", headers={"X-API-Key": "secret"})
    assert response.status_code == 200


def test_docs_are_not_protected(monkeypatch: pytest.MonkeyPatch) -> None:
    """Test that documentation endpoints stay accessible."""
    monkeypatch.setattr("vremenar.api.auth.api_key", "secret")
    assert client.get("/docs").status_code == 200
    assert client.get("/openapi.json").status_code == 200


def test_security_scheme_in_schema() -> None:
    """Test that the API key scheme is advertised in the OpenAPI schema."""
    schema = client.get("/openapi.json").json()
    assert "APIKeyHeader" in schema["components"]["securitySchemes"]
    assert schema["paths"]["/version"]["get"]["security"] == [{"APIKeyHeader": []}]
