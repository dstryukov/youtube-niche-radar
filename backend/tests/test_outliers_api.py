from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.videos import router as videos_router
from app.db.session import get_db


@pytest.fixture
def mock_db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.execute.return_value.all.return_value = []
    db.scalar.return_value = None
    return db


@pytest.fixture
def client_with_mock_db(client: TestClient, mock_db: MagicMock) -> TestClient:
    from app.main import app

    app.dependency_overrides[get_db] = lambda: mock_db
    yield client
    app.dependency_overrides.clear()


def test_outliers_basic_returns_list(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_outliers_with_limit(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?limit=25")
    assert response.status_code == 200


def test_outliers_with_min_score(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?min_outlier_score=0.5")
    assert response.status_code == 200


def test_outliers_with_small_channel_breakout(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?small_channel_breakout=true")
    assert response.status_code == 200


def test_outliers_with_format_label(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?format_label=testing")
    assert response.status_code == 200


def test_outliers_with_niche_label(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?niche_label=testing")
    assert response.status_code == 200


def test_outliers_with_faceless_filter(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?is_faceless_friendly=true")
    assert response.status_code == 200


def test_outliers_with_ai_filter(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?is_ai_friendly=false")
    assert response.status_code == 200


def test_outliers_with_sort_by_views(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?sort=views_per_day")
    assert response.status_code == 200


def test_outliers_with_sort_by_published(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?sort=published_at")
    assert response.status_code == 200


def test_outliers_with_sort_by_multiplier(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?sort=outlier_multiplier")
    assert response.status_code == 200


def test_outliers_invalid_sort_returns_400(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?sort=invalid_field")
    assert response.status_code == 400
    body = response.json()
    assert "detail" in body
    assert "invalid" in body["detail"].lower()


def test_outliers_all_filters_together(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get(
        "/videos/outliers"
        "?min_outlier_score=0.3"
        "&small_channel_breakout=true"
        "&format_label=testing"
        "&niche_label=testing"
        "&is_faceless_friendly=true"
        "&is_ai_friendly=false"
        "&sort=outlier_score"
        "&limit=10"
    )
    assert response.status_code == 200
