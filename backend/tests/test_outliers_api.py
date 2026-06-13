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


def test_outliers_with_min_views(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?min_views=1000")
    assert response.status_code == 200


def test_outliers_with_max_views(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?max_views=10000")
    assert response.status_code == 200


def test_outliers_with_views_range(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?min_views=1000&max_views=10000")
    assert response.status_code == 200


def test_outliers_min_views_greater_than_max_returns_400(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?min_views=10000&max_views=1000")
    assert response.status_code == 400


def test_outliers_with_min_views_per_day(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?min_views_per_day=100.5")
    assert response.status_code == 200


def test_outliers_with_views_per_day_range(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?min_views_per_day=100&max_views_per_day=5000")
    assert response.status_code == 200


def test_outliers_min_views_per_day_greater_than_max_returns_400(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?min_views_per_day=5000&max_views_per_day=100")
    assert response.status_code == 400


def test_outliers_with_published_after(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?published_after=2024-01-01T00:00:00")
    assert response.status_code == 200


def test_outliers_with_published_before(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?published_before=2025-01-01T00:00:00")
    assert response.status_code == 200


def test_outliers_published_after_greater_than_before_returns_400(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get(
        "/videos/outliers?published_after=2025-01-01T00:00:00&published_before=2024-01-01T00:00:00"
    )
    assert response.status_code == 400


def test_outliers_sort_by_latest_views(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?sort=latest_views")
    assert response.status_code == 200


def test_outliers_legacy_request_still_works(client_with_mock_db: TestClient) -> None:
    response = client_with_mock_db.get("/videos/outliers?limit=25")
    assert response.status_code == 200


def test_outliers_response_contains_format_fields(client_with_mock_db: TestClient, mock_db: MagicMock) -> None:
    from collections import namedtuple
    from datetime import datetime, timezone
    from unittest.mock import MagicMock as MM

    video = MM(
        id=1,
        youtube_video_id="test123",
        title="Test",
        channel_id=1,
        published_at=datetime.now(timezone.utc),
        thumbnail_url=None,
    )
    channel = MM(id=1, title="Test Channel", subscriber_count=1000)
    score = MM(
        latest_views=100000,
        views_per_day=5000.0,
        views_per_sub=100.0,
        channel_baseline_vpd=500.0,
        outlier_multiplier=10.0,
        outlier_score=1.0,
        repeatability_score=0.5,
        is_small_channel_breakout=False,
        explanation="Test explanation",
    )
    classification = MM(
        format_label="Reddit Story",
        niche_label="entertainment",
        hook_type=None,
        target_audience=None,
        is_faceless_friendly=True,
        is_ai_friendly=True,
        classifier_version="rule_v1",
        repeatability_score=None,
        adaptation_ideas=None,
        confidence=None,
        rationale=None,
        model="stub",
    )

    MockRow = namedtuple("MockRow", ["Video", "Channel", "VideoScore", "AIClassification"])
    row = MockRow(Video=video, Channel=channel, VideoScore=score, AIClassification=classification)

    mock_db.execute.return_value.all.return_value = [row]
    baseline_row = MM()
    baseline_row.video_count = 10
    baseline_row.avg_views = 18000.0
    baseline_row.median_views = 15000.0
    baseline_row.p75_views = 32000.0
    baseline_row.p90_views = 87000.0
    mock_db.execute.return_value.one.return_value = baseline_row

    response = client_with_mock_db.get("/videos/outliers")
    assert response.status_code == 200
    data = response.json()
    assert len(data) > 0
    item = data[0]
    assert item["classification"] is not None
    assert item["classification"]["format_label"] == "Reddit Story"
    assert item["classification"]["is_faceless_friendly"] is True
    assert item["classification"]["is_ai_friendly"] is True
    assert item["classification"]["classifier_version"] == "rule_v1"


def test_outliers_response_contains_explain_fields(client_with_mock_db: TestClient, mock_db: MagicMock) -> None:
    from collections import namedtuple
    from datetime import datetime, timezone

    video = MagicMock(
        id=1,
        youtube_video_id="test123",
        title="Test",
        channel_id=1,
        published_at=datetime.now(timezone.utc),
        thumbnail_url=None,
    )
    channel = MagicMock(id=1, title="Test Channel", subscriber_count=1000)
    score = MagicMock(
        latest_views=100000,
        views_per_day=5000.0,
        views_per_sub=100.0,
        channel_baseline_vpd=500.0,
        outlier_multiplier=10.0,
        outlier_score=1.0,
        repeatability_score=0.5,
        is_small_channel_breakout=False,
        explanation="Test explanation",
    )

    MockRow = namedtuple("MockRow", ["Video", "Channel", "VideoScore", "AIClassification"])
    row = MockRow(Video=video, Channel=channel, VideoScore=score, AIClassification=None)

    mock_db.execute.return_value.all.return_value = [row]

    baseline_row = MagicMock()
    baseline_row.video_count = 10
    baseline_row.avg_views = 18000.0
    baseline_row.median_views = 15000.0
    baseline_row.p75_views = 32000.0
    baseline_row.p90_views = 87000.0
    mock_db.execute.return_value.one.return_value = baseline_row

    response = client_with_mock_db.get("/videos/outliers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    item = data[0]
    assert "channel_avg_views" in item
    assert "channel_median_views" in item
    assert "ratio_to_avg" in item
    assert "ratio_to_median" in item
    assert "percentile_bucket" in item
