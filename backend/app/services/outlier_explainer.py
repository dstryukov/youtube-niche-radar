from __future__ import annotations

from sqlalchemy.orm import Session

from app.models import Video
from app.services.channel_baseline import compute_channel_baseline


def _safe_ratio(numerator: int | None, denominator: int | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return round(numerator / denominator, 1)


def _percentile_bucket(
    latest_views: int,
    p75_views: int | None,
    p90_views: int | None,
) -> str:
    if p90_views is not None and latest_views >= p90_views:
        return "top_10_percent"
    if p75_views is not None and latest_views >= p75_views:
        return "top_25_percent"
    return "normal"


def explain_video(db: Session, video: Video) -> dict | None:
    baseline = compute_channel_baseline(db, video.channel_id)
    if not baseline:
        return None

    score = video.score
    if not score or score.latest_views is None:
        return None

    latest_views = score.latest_views
    avg_views = baseline["avg_views"]
    median_views = baseline["median_views"]
    p75_views = baseline["p75_views"]
    p90_views = baseline["p90_views"]

    return {
        "avg_views": avg_views,
        "median_views": median_views,
        "ratio_to_avg": _safe_ratio(latest_views, avg_views),
        "ratio_to_median": _safe_ratio(latest_views, median_views),
        "percentile_bucket": _percentile_bucket(latest_views, p75_views, p90_views),
    }
