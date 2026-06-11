from __future__ import annotations

from fastapi.testclient import TestClient


def test_create_channel_empty_body_returns_400(client: TestClient) -> None:
    response = client.post("/channels", json={})
    assert response.status_code == 400
    assert "channel_id or handle" in response.json()["detail"]


def test_create_channel_missing_fields_returns_400(client: TestClient) -> None:
    response = client.post("/channels", json={"handle": None, "channel_id": None})
    assert response.status_code == 400
    assert "channel_id or handle" in response.json()["detail"]


def test_create_channel_invalid_type_returns_422(client: TestClient) -> None:
    response = client.post("/channels", json={"channel_id": 123})
    assert response.status_code == 422


def test_create_channel_handle_only_body(client: TestClient) -> None:
    response = client.post("/channels", json={"handle": "@test"})
    assert response.status_code in (200, 400)


def test_list_channels_returns_list(client: TestClient) -> None:
    response = client.get("/channels")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_list_channels_with_filter(client: TestClient) -> None:
    response = client.get("/channels?status=active&limit=50")
    assert response.status_code == 200


def test_sync_channel_not_found(client: TestClient) -> None:
    response = client.post("/channels/99999/sync")
    assert response.status_code == 404


def test_sync_all_returns_empty(client: TestClient) -> None:
    response = client.post("/channels/sync-all")
    assert response.status_code == 200
    body = response.json()
    assert "queued" in body
    assert "tasks" in body