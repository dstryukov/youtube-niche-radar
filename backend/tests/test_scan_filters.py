from __future__ import annotations

from datetime import UTC, datetime, timedelta

from app.services.ingest import _is_candidate_match


def _make_item(
    view_count: int | None = 5000,
    published_at: str | None = None,
) -> dict:
    if published_at is None:
        published_at = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    return {
        "id": "test_video_id",
        "statistics": {"viewCount": str(view_count) if view_count is not None else None},
        "snippet": {"publishedAt": published_at},
    }


def test_match_no_filters() -> None:
    item = _make_item(view_count=5000)
    assert _is_candidate_match(item, {}) is True


def test_match_min_views_above() -> None:
    item = _make_item(view_count=5000)
    assert _is_candidate_match(item, {"min_views": 1000}) is True


def test_match_min_views_below() -> None:
    item = _make_item(view_count=500)
    assert _is_candidate_match(item, {"min_views": 1000}) is False


def test_match_max_views_below() -> None:
    item = _make_item(view_count=500)
    assert _is_candidate_match(item, {"max_views": 1000}) is True


def test_match_max_views_above() -> None:
    item = _make_item(view_count=5000)
    assert _is_candidate_match(item, {"max_views": 1000}) is False


def test_match_views_range() -> None:
    item = _make_item(view_count=5000)
    assert _is_candidate_match(item, {"min_views": 1000, "max_views": 10000}) is True


def test_match_views_range_outside() -> None:
    item = _make_item(view_count=50000)
    assert _is_candidate_match(item, {"min_views": 1000, "max_views": 10000}) is False


def test_match_min_views_per_day() -> None:
    item = _make_item(view_count=10000, published_at=(datetime.now(UTC) - timedelta(days=10)).isoformat())
    assert _is_candidate_match(item, {"min_views_per_day": 500}) is True


def test_match_min_views_per_day_below() -> None:
    item = _make_item(view_count=100, published_at=(datetime.now(UTC) - timedelta(days=10)).isoformat())
    assert _is_candidate_match(item, {"min_views_per_day": 500}) is False


def test_match_published_after() -> None:
    recent = (datetime.now(UTC) - timedelta(days=5)).isoformat()
    item = _make_item(published_at=recent)
    cutoff = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    assert _is_candidate_match(item, {"published_after": cutoff}) is True


def test_match_published_after_too_old() -> None:
    old = (datetime.now(UTC) - timedelta(days=30)).isoformat()
    item = _make_item(published_at=old)
    cutoff = (datetime.now(UTC) - timedelta(days=10)).isoformat()
    assert _is_candidate_match(item, {"published_after": cutoff}) is False


def test_match_null_views_with_filter() -> None:
    item = _make_item(view_count=None)
    assert _is_candidate_match(item, {"min_views": 1000}) is False


def test_match_all_filters() -> None:
    published = (datetime.now(UTC) - timedelta(days=15)).isoformat()
    item = _make_item(view_count=5000, published_at=published)
    opts = {
        "min_views": 1000,
        "max_views": 10000,
        "min_views_per_day": 100,
        "max_views_per_day": 1000,
        "published_after": (datetime.now(UTC) - timedelta(days=30)).isoformat(),
        "published_before": (datetime.now(UTC) - timedelta(days=1)).isoformat(),
    }
    assert _is_candidate_match(item, opts) is True
