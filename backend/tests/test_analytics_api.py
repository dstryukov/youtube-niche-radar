from __future__ import annotations

from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.analytics import router as analytics_router
from app.db.session import get_db


@pytest.fixture
def mock_db() -> MagicMock:
    db = MagicMock(spec=Session)
    db.execute.return_value.all.return_value = []
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
    from collections import namedtuple

    Row = namedtuple("Row", ["format_label", "videos", "avg_outlier_score", "avg_views"])
    mock_db.execute.return_value.all.return_value = [
        Row("Reddit Story", 120, 2.8, 54000.0),
        Row("Top List", 85, 1.5, 32000.0),
    ]

    response = client_with_mock_db.get("/analytics/formats")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["format_label"] == "Reddit Story"
    assert data[0]["videos"] == 120
    assert data[0]["avg_outlier_score"] == 2.8
    assert data[0]["avg_views"] == 54000


def test_analytics_formats_empty(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/analytics/formats")
    assert response.status_code == 200
    assert response.json() == []
