from __future__ import annotations

from unittest.mock import MagicMock
from collections import namedtuple

from sqlalchemy.orm import Session

from app.services.channel_baseline import compute_channel_baseline


def _mock_execute_one(row_data: dict | None):
    Row = namedtuple("Row", row_data.keys() if row_data else [])
    row = Row(**row_data) if row_data else Row()

    mock_execute = MagicMock()
    mock_execute.one.return_value = row
    return mock_execute


def test_baseline_multiple_videos() -> None:
    db = MagicMock(spec=Session)
    db.execute.return_value = _mock_execute_one(
        {
            "video_count": 4,
            "avg_views": 27500.0,
            "median_views": 22500.0,
            "p75_views": 42500.0,
            "p90_views": 82500.0,
        }
    )

    result = compute_channel_baseline(db, channel_id=1)
    assert result is not None
    assert result["video_count"] == 4
    assert result["avg_views"] == 27500
    assert result["median_views"] == 22500
    assert result["p75_views"] == 42500
    assert result["p90_views"] == 82500


def test_baseline_empty() -> None:
    db = MagicMock(spec=Session)
    db.execute.return_value = _mock_execute_one(
        {
            "video_count": 0,
            "avg_views": None,
            "median_views": None,
            "p75_views": None,
            "p90_views": None,
        }
    )

    result = compute_channel_baseline(db, channel_id=1)
    assert result is None


def test_baseline_no_scores() -> None:
    db = MagicMock(spec=Session)
    db.execute.return_value = _mock_execute_one(
        {
            "video_count": 0,
            "avg_views": None,
            "median_views": None,
            "p75_views": None,
            "p90_views": None,
        }
    )

    result = compute_channel_baseline(db, channel_id=999)
    assert result is None


def test_baseline_avg_rounded() -> None:
    db = MagicMock(spec=Session)
    db.execute.return_value = _mock_execute_one(
        {
            "video_count": 3,
            "avg_views": 18333.333,
            "median_views": 15000.0,
            "p75_views": 24000.0,
            "p90_views": 28000.0,
        }
    )

    result = compute_channel_baseline(db, channel_id=1)
    assert result is not None
    assert result["avg_views"] == 18333
