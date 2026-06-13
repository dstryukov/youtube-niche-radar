from __future__ import annotations

from collections import namedtuple
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api.routes.analytics import router as analytics_router
from app.db.session import get_db
from app.services.niche_analytics import get_niche_catalog, get_niche_coverage


def _mock_row(**kwargs):
    Row = namedtuple("Row", kwargs.keys())
    return Row(**kwargs)


def _make_db(*, execute_rows: list | None = None, scalar_values: list | None = None) -> MagicMock:
    db = MagicMock(spec=Session)
    if execute_rows is not None:
        mock_exec = MagicMock()
        mock_exec.all.return_value = execute_rows
        db.execute.return_value = mock_exec
    else:
        db.execute.return_value = MagicMock(all=MagicMock(return_value=[]))

    if scalar_values is not None:
        db.scalar = MagicMock(side_effect=scalar_values)
    else:
        db.scalar = MagicMock(return_value=None)
    return db


class TestNicheCatalog:
    def test_empty_db(self) -> None:
        db = _make_db(execute_rows=[])
        result = get_niche_catalog(db)
        assert result == []

    def test_with_data(self) -> None:
        rows = [
            _mock_row(
                niche_label="AI",
                channels=5,
                videos=100,
                outliers=10,
                avg_outlier_score=1.5,
                avg_views=50000.0,
            ),
            _mock_row(
                niche_label="History",
                channels=3,
                videos=50,
                outliers=5,
                avg_outlier_score=0.8,
                avg_views=30000.0,
            ),
        ]
        db = _make_db(execute_rows=rows)
        result = get_niche_catalog(db)
        assert len(result) == 2
        assert result[0]["niche"] == "AI"
        assert result[0]["videos"] == 100
        assert result[0]["outliers"] == 10
        assert result[0]["avg_outlier_score"] == 1.5
        assert result[0]["avg_views"] == 50000
        assert result[1]["niche"] == "History"


class TestNicheCoverage:
    def test_returns_structure(self) -> None:
        db = MagicMock(spec=Session)
        db.scalar = MagicMock(side_effect=[100, 80, 20])
        result = get_niche_coverage(db)
        assert result["videos_total"] == 100
        assert result["classified"] == 80
        assert result["other"] == 20
        assert result["coverage_percent"] == 80.0

    def test_zero_total(self) -> None:
        db = MagicMock(spec=Session)
        db.scalar = MagicMock(side_effect=[0, 0, 0])
        result = get_niche_coverage(db)
        assert result["videos_total"] == 0
        assert result["coverage_percent"] == 0.0


class TestNicheAnalyticsAPI:
    @pytest.fixture
    def mock_db(self) -> MagicMock:
        db = MagicMock(spec=Session)
        mock_exec = MagicMock()
        mock_exec.all.return_value = []
        db.execute.return_value = mock_exec
        db.scalar = MagicMock(return_value=None)
        return db

    @pytest.fixture
    def client_with_mock_db(self, client: TestClient, mock_db: MagicMock) -> TestClient:
        from app.main import app
        app.dependency_overrides[get_db] = lambda: mock_db
        yield client
        app.dependency_overrides.clear()

    def test_analytics_niches_returns_list(self, client_with_mock_db: TestClient) -> None:
        response = client_with_mock_db.get("/analytics/niches")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_analytics_niches_trending(self, client_with_mock_db: TestClient) -> None:
        response = client_with_mock_db.get("/analytics/niches/trending")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_analytics_niches_coverage(self, client_with_mock_db: TestClient) -> None:
        response = client_with_mock_db.get("/analytics/niches/coverage")
        assert response.status_code == 200
        data = response.json()
        assert "videos_total" in data
        assert "classified" in data
        assert "other" in data
        assert "coverage_percent" in data

    def test_analytics_niche_outliers(self, client_with_mock_db: TestClient) -> None:
        response = client_with_mock_db.get("/analytics/niches/AI/outliers")
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_analytics_reclassify_niches(self, client_with_mock_db: TestClient) -> None:
        with patch("app.api.routes.maintenance.reclassify_all_niches") as mock_reclassify:
            mock_reclassify.return_value = {"videos_processed": 100, "updated": 95, "failed": 0}
            response = client_with_mock_db.post("/maintenance/reclassify-niches")
            assert response.status_code == 200
            data = response.json()
            assert data["videos_processed"] == 100
            assert data["updated"] == 95
            assert data["failed"] == 0


class TestReclassifyNichesService:
    def test_reclassify_niches(self) -> None:
        from app.services.reclassify_niches import reclassify_all_niches

        mock_db = MagicMock()
        mock_db.scalars.return_value.all.return_value = [1, 2]

        video1 = MagicMock()
        video1.id = 1
        video1.title = "chatgpt changed my life"
        video1.description = "ai content"
        video1.channel.title = "TechGuru"

        video2 = MagicMock()
        video2.id = 2
        video2.title = "random cooking video"
        video2.description = None
        video2.channel.title = "Chef"

        mock_db.get.side_effect = lambda _, vid: video1 if vid == 1 else video2
        mock_db.scalar.return_value = None

        result = reclassify_all_niches(mock_db)

        assert result["videos_processed"] == 2
        assert result["updated"] == 2
        assert result["failed"] == 0
        mock_db.commit.assert_called_once()
