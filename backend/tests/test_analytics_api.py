from __future__ import annotations

from collections import namedtuple
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.analytics import router as analytics_router
from app.db.session import get_db


@pytest.fixture
def mock_db() -> MagicMock:
    db = MagicMock(spec=Session)
    mock_exec = MagicMock()
    mock_exec.all.return_value = []
    db.execute.return_value = mock_exec
    db.scalar = MagicMock(return_value=None)
    return db


@pytest.fixture
def client_with_mock_db(client: TestClient, mock_db: MagicMock) -> TestClient:
    from app.main import app

    app.dependency_overrides[get_db] = lambda: mock_db
    yield client
    app.dependency_overrides.clear()


def test_analytics_formats_returns_list(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/analytics/formats")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analytics_formats_with_data(client_with_mock_db: TestClient, mock_db: MagicMock) -> None:
    Row = namedtuple("Row", [
        "format_label", "videos", "avg_outlier_score", "avg_views",
        "faceless_count", "ai_friendly_count",
    ])
    mock_db.execute.return_value.all.return_value = [
        Row("Reddit Story", 120, 2.8, 54000.0, 80, 60),
        Row("Top List", 85, 1.5, 32000.0, 40, 20),
    ]

    response = client_with_mock_db.get("/analytics/formats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["format_label"] == "Reddit Story"
    assert data[0]["videos"] == 120
    assert data[0]["avg_outlier_score"] == 2.8
    assert data[0]["avg_views"] == 54000
    assert data[0]["faceless_count"] == 80
    assert data[0]["ai_friendly_count"] == 60


def test_analytics_formats_empty(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/analytics/formats")
    assert response.status_code == 200
    assert response.json() == []


def test_analytics_formats_trending(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/analytics/formats/trending?period_days=30")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_analytics_format_detail_not_found(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/analytics/formats/nonexistent")
    assert response.status_code == 404


def test_analytics_format_detail_found(client_with_mock_db: TestClient, mock_db: MagicMock) -> None:
    from app.models import Format
    mock_format = MagicMock(spec=Format)
    mock_format.label = "test_format"
    mock_format.description = "Test description"
    mock_format.is_faceless_friendly = True
    mock_format.is_ai_friendly = True
    mock_format.repeatability_prior = 0.8

    mock_db.scalar = MagicMock(side_effect=[mock_format, 6, 4])

    stats_row = MagicMock(
        videos_count=10,
        avg_views=45000.0,
        median_views=40000.0,
        max_views=100000,
        avg_outlier_score=0.75,
        avg_repeatability=0.8,
    )
    exec_stats = MagicMock()
    exec_stats.one.return_value = stats_row
    exec_channels = MagicMock()
    exec_channels.all.return_value = []
    mock_db.execute = MagicMock(side_effect=[exec_stats, exec_channels])

    response = client_with_mock_db.get("/analytics/formats/test_format")
    assert response.status_code == 200
    data = response.json()
    assert data["format_label"] == "test_format"
    assert data["videos_count"] == 10
