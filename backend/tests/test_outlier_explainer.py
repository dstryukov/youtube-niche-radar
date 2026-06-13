from __future__ import annotations

from unittest.mock import MagicMock, PropertyMock

from sqlalchemy.orm import Session

from app.models import Video, VideoScore
from app.services.outlier_explainer import explain_video, _percentile_bucket, _safe_ratio


def test_percentile_bucket_top_10() -> None:
    assert _percentile_bucket(100_000, p75_views=40_000, p90_views=80_000) == "top_10_percent"
    assert _percentile_bucket(80_000, p75_views=40_000, p90_views=80_000) == "top_10_percent"


def test_percentile_bucket_top_25() -> None:
    assert _percentile_bucket(60_000, p75_views=40_000, p90_views=80_000) == "top_25_percent"
    assert _percentile_bucket(40_000, p75_views=40_000, p90_views=80_000) == "top_25_percent"


def test_percentile_bucket_normal() -> None:
    assert _percentile_bucket(10_000, p75_views=40_000, p90_views=80_000) == "normal"
    assert _percentile_bucket(39_999, p75_views=40_000, p90_views=80_000) == "normal"


def test_percentile_bucket_no_p90() -> None:
    assert _percentile_bucket(100_000, p75_views=40_000, p90_views=None) == "top_25_percent"
    assert _percentile_bucket(10_000, p75_views=40_000, p90_views=None) == "normal"


def test_percentile_bucket_no_p75_no_p90() -> None:
    assert _percentile_bucket(100_000, p75_views=None, p90_views=None) == "normal"


def test_safe_ratio() -> None:
    assert _safe_ratio(100, 50) == 2.0
    assert _safe_ratio(100, 0) is None
    assert _safe_ratio(None, 50) is None
    assert _safe_ratio(100, None) is None
    assert _safe_ratio(0, 100) == 0.0


def test_explain_video_with_baseline() -> None:
    video = MagicMock(spec=Video)
    video.channel_id = 1
    score = MagicMock(spec=VideoScore)
    score.latest_views = 100_000
    type(video).score = PropertyMock(return_value=score)

    db = MagicMock(spec=Session)
    db.execute.return_value.one.return_value = type(
        "Row",
        (),
        {
            "video_count": 10,
            "avg_views": 18000.0,
            "median_views": 15000.0,
            "p75_views": 32000.0,
            "p90_views": 87000.0,
        },
    )

    result = explain_video(db, video)
    assert result is not None
    assert result["avg_views"] == 18000
    assert result["median_views"] == 15000
    assert result["ratio_to_avg"] == 5.6
    assert result["ratio_to_median"] == 6.7
    assert result["percentile_bucket"] == "top_10_percent"


def test_explain_video_no_score() -> None:
    video = MagicMock(spec=Video)
    video.channel_id = 1
    type(video).score = PropertyMock(return_value=None)

    db = MagicMock(spec=Session)
    db.execute.return_value.one.return_value = type(
        "Row",
        (),
        {
            "video_count": 5,
            "avg_views": 10000.0,
            "median_views": 8000.0,
            "p75_views": 15000.0,
            "p90_views": 25000.0,
        },
    )

    result = explain_video(db, video)
    assert result is None


def test_explain_video_no_baseline() -> None:
    video = MagicMock(spec=Video)
    video.channel_id = 999
    score = MagicMock(spec=VideoScore)
    score.latest_views = 1000
    type(video).score = PropertyMock(return_value=score)

    db = MagicMock(spec=Session)
    db.execute.return_value.one.return_value = type(
        "Row",
        (),
        {
            "video_count": 0,
            "avg_views": None,
            "median_views": None,
            "p75_views": None,
            "p90_views": None,
        },
    )

    result = explain_video(db, video)
    assert result is None
