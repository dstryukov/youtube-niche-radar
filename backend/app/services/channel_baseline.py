from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Video, VideoScore


def compute_channel_baseline(db: Session, channel_id: int) -> dict | None:
    stmt = (
        select(
            func.count(VideoScore.id).label("video_count"),
            func.avg(VideoScore.latest_views).label("avg_views"),
            func.percentile_cont(0.5)
            .within_group(VideoScore.latest_views.asc())
            .label("median_views"),
            func.percentile_cont(0.75)
            .within_group(VideoScore.latest_views.asc())
            .label("p75_views"),
            func.percentile_cont(0.90)
            .within_group(VideoScore.latest_views.asc())
            .label("p90_views"),
        )
        .join(Video, Video.id == VideoScore.video_id)
        .where(
            Video.channel_id == channel_id,
            VideoScore.latest_views.isnot(None),
        )
    )

    row = db.execute(stmt).one()

    if row.video_count == 0 or row.avg_views is None:
        return None

    return {
        "video_count": row.video_count,
        "avg_views": round(row.avg_views),
        "median_views": round(row.median_views) if row.median_views is not None else None,
        "p75_views": round(row.p75_views) if row.p75_views is not None else None,
        "p90_views": round(row.p90_views) if row.p90_views is not None else None,
    }
