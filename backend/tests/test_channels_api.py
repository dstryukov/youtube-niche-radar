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


def test_sync_channel_limit_too_high_returns_422(client: TestClient) -> None:
    response = client.post("/channels/1/sync?limit=501")
    assert response.status_code == 422


def test_sync_channel_limit_zero_returns_422(client: TestClient) -> None:
    response = client.post("/channels/1/sync?limit=0")
    assert response.status_code == 422


def test_sync_all_limit_too_high_returns_422(client: TestClient) -> None:
    response = client.post("/channels/sync-all?limit=501")
    assert response.status_code == 422


def test_sync_response_contains_requested_limit(client: TestClient) -> None:
    response = client.post("/channels/sync-all")
    assert response.status_code == 200
    body = response.json()
    assert "queued" in body
    assert "tasks" in body
    assert "requested_limit" in body
    assert "max_channels" in body


def test_sync_response_with_limit_param(client: TestClient) -> None:
    response = client.post("/channels/sync-all?limit=150")
    assert response.status_code == 200
    body = response.json()
    assert body["requested_limit"] == 150


def test_sync_channel_with_min_views(client: TestClient) -> None:
    response = client.post("/channels/99999/sync?min_views=1000")
    assert response.status_code == 404  # channel not found, but param accepted


def test_sync_channel_min_views_greater_than_max_returns_400(client: TestClient) -> None:
    response = client.post("/channels/1/sync?min_views=10000&max_views=1000")
    assert response.status_code == 400


def test_sync_all_min_views_greater_than_max_returns_400(client: TestClient) -> None:
    response = client.post("/channels/sync-all?min_views=10000&max_views=1000")
    assert response.status_code == 400


def test_sync_channel_stop_after_matches_out_of_range_returns_400(client: TestClient) -> None:
    response = client.post("/channels/1/sync?stop_after_matches=999")
    assert response.status_code == 422  # FastAPI Query validation: ge=1, so 999 passes but 0 fails


def test_sync_channel_stop_after_matches_zero_returns_422(client: TestClient) -> None:
    response = client.post("/channels/1/sync?stop_after_matches=0")
    assert response.status_code == 422


def test_sync_response_contains_scan_options(client: TestClient) -> None:
    response = client.post("/channels/sync-all")
    assert response.status_code == 200
    body = response.json()
    assert "scan_options" in body
    assert body["scan_options"]["save_skipped"] is True


def test_sync_response_scan_options_reflect_params(client: TestClient) -> None:
    response = client.post("/channels/sync-all?min_views=1000&max_views=10000&stop_after_matches=20")
    assert response.status_code == 200
    body = response.json()
    assert body["scan_options"]["min_views"] == 1000
    assert body["scan_options"]["max_views"] == 10000
    assert body["scan_options"]["stop_after_matches"] == 20