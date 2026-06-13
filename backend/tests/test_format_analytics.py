from __future__ import annotations

from collections import namedtuple
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models import Format
from app.services.format_analytics import get_format_catalog, get_format_details, get_trending_formats


def _mock_row(**kwargs):
    Row = namedtuple("Row", kwargs.keys())
    return Row(**kwargs)


def _make_db(
    *,
    execute_rows: list | None = None,
    execute_one: dict | None = None,
    scalar: int | None = None,
    format_row: Format | None = None,
) -> MagicMock:
    db = MagicMock(spec=Session)

    if execute_rows is not None:
        mock_exec = MagicMock()
        mock_exec.all.return_value = execute_rows
        db.execute.return_value = mock_exec
    elif execute_one is not None:
        mock_exec = MagicMock()
        mock_exec.one.return_value = _mock_row(**execute_one)
        db.execute.return_value = mock_exec
    else:
        db.execute.return_value = MagicMock(all=MagicMock(return_value=[]))

    db.scalar = MagicMock(return_value=scalar if scalar is not None else 0)

    if format_row is not None:
        db.scalar = MagicMock(return_value=format_row)

    return db


class TestGetFormatCatalog:
    def test_empty_db(self) -> None:
        db = _make_db(execute_rows=[])
        result = get_format_catalog(db)
        assert result == []

    def test_with_data(self) -> None:
        rows = [
            _mock_row(
                format_label="tutorial / guide",
                videos=10,
                avg_outlier_score=0.85,
                avg_views=50000.0,
                faceless_count=8,
                ai_friendly_count=6,
            ),
            _mock_row(
                format_label="review / comparison",
                videos=5,
                avg_outlier_score=0.45,
                avg_views=30000.0,
                faceless_count=3,
                ai_friendly_count=0,
            ),
        ]
        db = _make_db(execute_rows=rows)
        result = get_format_catalog(db)
        assert len(result) == 2
        assert result[0]["format_label"] == "tutorial / guide"
        assert result[0]["videos"] == 10
        assert result[0]["avg_views"] == 50000
        assert result[0]["faceless_count"] == 8
        assert result[0]["ai_friendly_count"] == 6


class TestGetFormatDetails:
    def test_format_not_found(self) -> None:
        db = MagicMock(spec=Session)
        db.scalar = MagicMock(return_value=None)
        result = get_format_details(db, "nonexistent", 30)
        assert result is None

    def test_format_found(self) -> None:
        fmt = Format(label="tutorial / guide", description="A how-to format", is_faceless_friendly=True, is_ai_friendly=True, repeatability_prior=0.85)

        stats_row = _mock_row(
            videos_count=10,
            avg_views=45000.0,
            median_views=40000.0,
            max_views=100000,
            avg_outlier_score=0.75,
            avg_repeatability=0.8,
        )

        channel_rows = [
            _mock_row(channel_title="Channel A", videos_count=5),
            _mock_row(channel_title="Channel B", videos_count=3),
        ]

        db = MagicMock(spec=Session)
        db.scalar = MagicMock(side_effect=[fmt, 6, 4])

        exec_stats = MagicMock()
        exec_stats.one.return_value = stats_row

        exec_channels = MagicMock()
        exec_channels.all.return_value = channel_rows

        db.execute = MagicMock(side_effect=[exec_stats, exec_channels])

        result = get_format_details(db, "tutorial / guide", 30)
        assert result is not None
        assert result["format_label"] == "tutorial / guide"
        assert result["videos_count"] == 10
        assert result["avg_views"] == 45000
        assert result["median_views"] == 40000
        assert result["max_views"] == 100000
        assert result["avg_outlier_score"] == 0.75
        assert result["avg_repeatability"] == 0.8
        assert result["trend"] == 50.0
        assert len(result["top_channels"]) == 2


class TestGetTrendingFormats:
    def test_empty_db(self) -> None:
        db = _make_db(execute_rows=[])
        result = get_trending_formats(db, 30)
        assert result == []

    def test_returns_sorted_by_growth(self) -> None:
        rows = [
            _mock_row(format_label="reddit_story", recent_count=20, avg_views=60000.0),
            _mock_row(format_label="tutorial / guide", recent_count=15, avg_views=40000.0),
            _mock_row(format_label="reaction", recent_count=5, avg_views=10000.0),
        ]
        db = _make_db(execute_rows=rows)
        db.scalar = MagicMock(side_effect=[5, 10, 15])
        result = get_trending_formats(db, 30)
        assert len(result) == 3
        assert result[0]["format_label"] == "reddit_story"
        assert result[0]["growth_rate"] == 300.0
        assert result[1]["format_label"] == "tutorial / guide"
        assert result[1]["growth_rate"] == 50.0
        assert result[2]["format_label"] == "reaction"
        assert result[2]["growth_rate"] < 0
