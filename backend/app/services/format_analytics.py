from __future__ import annotations

from datetime import datetime

from sqlalchemy import Date, case, cast, desc, func, select
from sqlalchemy.orm import Session

from app.models import AIClassification, Channel, Format, Video, VideoScore


def get_format_catalog(db: Session) -> list[dict]:
    fmt_count = func.count(AIClassification.id).label("videos")
    faceless_sum = func.sum(case((AIClassification.is_faceless_friendly.is_(True), 1), else_=0))
    ai_sum = func.sum(case((AIClassification.is_ai_friendly.is_(True), 1), else_=0))

    rows = db.execute(
        select(
            AIClassification.format_label,
            fmt_count,
            func.avg(VideoScore.outlier_score).label("avg_outlier_score"),
            func.avg(VideoScore.latest_views).label("avg_views"),
            faceless_sum.label("faceless_count"),
            ai_sum.label("ai_friendly_count"),
        )
        .join(Video, Video.id == AIClassification.video_id)
        .join(VideoScore, VideoScore.video_id == Video.id)
        .where(AIClassification.format_label.isnot(None))
        .group_by(AIClassification.format_label)
        .order_by(desc("videos"))
        .limit(50)
    ).all()

    return [
        {
            "format_label": row.format_label,
            "videos": row.videos,
            "avg_outlier_score": round(row.avg_outlier_score, 2) if row.avg_outlier_score is not None else None,
            "avg_views": round(row.avg_views) if row.avg_views is not None else None,
            "faceless_count": row.faceless_count or 0,
            "ai_friendly_count": row.ai_friendly_count or 0,
        }
        for row in rows
    ]


def get_format_details(db: Session, label: str, period_days: int = 30) -> dict | None:
    fmt = db.scalar(select(Format).where(Format.label == label))
    if not fmt:
        return None

    cutoff = func.now() - func.make_interval(0, 0, 0, period_days)
    stmt = (
        select(
            func.count(AIClassification.id).label("videos_count"),
            func.avg(VideoScore.latest_views).label("avg_views"),
            func.percentile_cont(0.5).within_group(VideoScore.latest_views.asc()).label("median_views"),
            func.max(VideoScore.latest_views).label("max_views"),
            func.avg(VideoScore.outlier_score).label("avg_outlier_score"),
            func.avg(AIClassification.repeatability_score).label("avg_repeatability"),
        )
        .join(Video, Video.id == AIClassification.video_id)
        .join(VideoScore, VideoScore.video_id == Video.id)
        .where(
            AIClassification.format_label == label,
            AIClassification.created_at >= cutoff,
            VideoScore.latest_views.isnot(None),
        )
    )
    stats = db.execute(stmt).one()

    half = period_days // 2
    recent_cutoff = func.now() - func.make_interval(0, 0, 0, half)
    half_ago = func.now() - func.make_interval(0, 0, 0, period_days)

    recent_count = db.scalar(
        select(func.count(AIClassification.id))
        .join(Video, Video.id == AIClassification.video_id)
        .where(
            AIClassification.format_label == label,
            AIClassification.created_at >= recent_cutoff,
        )
    ) or 1

    earlier_count = db.scalar(
        select(func.count(AIClassification.id))
        .join(Video, Video.id == AIClassification.video_id)
        .where(
            AIClassification.format_label == label,
            AIClassification.created_at >= half_ago,
            AIClassification.created_at < recent_cutoff,
        )
    ) or 1

    growth_rate = round((recent_count - earlier_count) / earlier_count * 100, 1)

    channel_rows = db.execute(
        select(
            Channel.title.label("channel_title"),
            func.count(AIClassification.id).label("videos_count"),
        )
        .join(Video, Video.id == AIClassification.video_id)
        .join(Channel, Channel.id == Video.channel_id)
        .where(AIClassification.format_label == label)
        .group_by(Channel.title)
        .order_by(desc("videos_count"))
        .limit(10)
    ).all()

    return {
        "format_label": fmt.label,
        "description": fmt.description,
        "is_faceless_friendly": fmt.is_faceless_friendly,
        "is_ai_friendly": fmt.is_ai_friendly,
        "repeatability_prior": fmt.repeatability_prior,
        "videos_count": stats.videos_count or 0,
        "avg_views": round(stats.avg_views) if stats.avg_views is not None else None,
        "median_views": round(stats.median_views) if stats.median_views is not None else None,
        "max_views": stats.max_views,
        "avg_outlier_score": round(stats.avg_outlier_score, 2) if stats.avg_outlier_score is not None else None,
        "avg_repeatability": round(stats.avg_repeatability, 2) if stats.avg_repeatability is not None else None,
        "trend": growth_rate,
        "top_channels": [
            {"channel_title": row.channel_title, "videos_count": row.videos_count}
            for row in channel_rows
        ],
    }


def get_trending_formats(db: Session, period_days: int = 30) -> list[dict]:
    half = period_days // 2
    now = func.now()
    recent_cutoff = now - func.make_interval(0, 0, 0, half)
    half_ago = now - func.make_interval(0, 0, 0, period_days)

    rows = db.execute(
        select(
            AIClassification.format_label,
            func.count(AIClassification.id).label("recent_count"),
            func.avg(VideoScore.latest_views).label("avg_views"),
        )
        .join(Video, Video.id == AIClassification.video_id)
        .join(VideoScore, VideoScore.video_id == Video.id)
        .where(
            AIClassification.format_label.isnot(None),
            AIClassification.created_at >= recent_cutoff,
        )
        .group_by(AIClassification.format_label)
        .order_by(desc(func.count(AIClassification.id)))
        .limit(50)
    ).all()

    result = []
    for row in rows:
        earlier_count = db.scalar(
            select(func.count(AIClassification.id))
            .where(
                AIClassification.format_label == row.format_label,
                AIClassification.created_at >= half_ago,
                AIClassification.created_at < recent_cutoff,
            )
        ) or 0
        denom = earlier_count if earlier_count > 0 else 1
        growth_rate = round((row.recent_count - earlier_count) / denom * 100, 1)
        result.append({
            "format_label": row.format_label,
            "video_count": row.recent_count,
            "growth_rate": growth_rate,
            "avg_views": round(row.avg_views) if row.avg_views is not None else None,
        })

    result.sort(key=lambda r: r["growth_rate"], reverse=True)
    return result[:10]
