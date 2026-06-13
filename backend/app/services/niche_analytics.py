from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from app.models import AIClassification, Channel, Video, VideoScore


def get_niche_catalog(db: Session) -> list[dict[str, Any]]:
    rows = (
        db.execute(
            select(
                AIClassification.niche_label,
                func.count(func.distinct(Video.channel_id)).label("channels"),
                func.count(func.distinct(AIClassification.video_id)).label("videos"),
                func.count(
                    func.distinct(AIClassification.video_id)
                ).filter(VideoScore.outlier_score > 0.3).label("outliers"),
                func.coalesce(func.avg(VideoScore.outlier_score), 0).label("avg_outlier_score"),
                func.coalesce(func.avg(VideoScore.latest_views), 0).label("avg_views"),
            )
            .join(Video, Video.id == AIClassification.video_id)
            .join(VideoScore, VideoScore.video_id == AIClassification.video_id)
            .where(AIClassification.niche_label.isnot(None))
            .group_by(AIClassification.niche_label)
            .order_by(func.count(func.distinct(AIClassification.video_id)).desc())
        )
        .all()
    )

    result = []
    for row in rows:
        result.append(
            {
                "niche": row.niche_label,
                "channels": row.channels,
                "videos": row.videos,
                "outliers": row.outliers,
                "avg_outlier_score": round(float(row.avg_outlier_score), 2),
                "avg_views": round(float(row.avg_views)),
            }
        )
    return result


def get_niche_growth(
    db: Session, period_days: int = 30
) -> dict[str, dict[str, int]]:
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=period_days)
    mid = cutoff + timedelta(days=period_days // 2)

    rows = (
        db.execute(
            select(
                AIClassification.niche_label,
                func.count(AIClassification.video_id).label("cnt"),
            )
            .join(Video, Video.id == AIClassification.video_id)
            .where(
                AIClassification.niche_label.isnot(None),
                cast(Video.published_at, Date) >= cast(cutoff, Date),
                cast(Video.published_at, Date) < cast(mid, Date),
            )
            .group_by(AIClassification.niche_label)
        )
        .all()
    )
    earlier: dict[str, int] = {row.niche_label: row.cnt for row in rows}

    rows = (
        db.execute(
            select(
                AIClassification.niche_label,
                func.count(AIClassification.video_id).label("cnt"),
            )
            .join(Video, Video.id == AIClassification.video_id)
            .where(
                AIClassification.niche_label.isnot(None),
                cast(Video.published_at, Date) >= cast(mid, Date),
                cast(Video.published_at, Date) <= cast(now, Date),
            )
            .group_by(AIClassification.niche_label)
        )
        .all()
    )
    recent: dict[str, int] = {row.niche_label: row.cnt for row in rows}

    niches: dict[str, dict[str, int]] = {}
    for label in set(list(earlier.keys()) + list(recent.keys())):
        niches[label] = {
            "earlier": earlier.get(label, 0),
            "recent": recent.get(label, 0),
        }
    return niches


def get_trending_niches(
    db: Session, period_days: int = 30
) -> list[dict[str, Any]]:
    growth_data = get_niche_growth(db, period_days)
    result = []
    for niche, counts in growth_data.items():
        earlier = counts["earlier"]
        recent = counts["recent"]
        if earlier > 0:
            growth_rate = round((recent - earlier) / earlier * 100, 1)
        else:
            growth_rate = round(recent * 100, 1) if recent > 0 else 0.0
        result.append({"niche": niche, "growth_rate": growth_rate})

    result.sort(key=lambda x: x["growth_rate"], reverse=True)
    return result


def get_niche_outliers(
    db: Session, niche: str, limit: int = 20
) -> list[dict[str, Any]]:
    from app.schemas import AIClassificationRead, OutlierRead

    from app.services.channel_baseline import compute_channel_baseline

    latest_class = (
        select(
            AIClassification.video_id,
            AIClassification.id.label("classification_id"),
        )
        .distinct(AIClassification.video_id)
        .order_by(AIClassification.video_id, AIClassification.created_at.desc())
        .subquery()
    )

    stmt = (
        select(Video, Channel, VideoScore, AIClassification)
        .join(Channel, Channel.id == Video.channel_id)
        .join(VideoScore, VideoScore.video_id == Video.id)
        .outerjoin(latest_class, latest_class.c.video_id == Video.id)
        .outerjoin(AIClassification, AIClassification.id == latest_class.c.classification_id)
        .where(AIClassification.niche_label == niche)
        .order_by(VideoScore.outlier_score.desc(), VideoScore.views_per_day.desc())
        .limit(limit)
    )

    rows = db.execute(stmt).all()
    channel_ids = {channel.id for _, channel, _, _ in rows}
    baselines: dict[int, dict | None] = {}
    for cid in channel_ids:
        if cid not in baselines:
            baselines[cid] = compute_channel_baseline(db, cid)

    def _explain_for(video, score):
        baseline = baselines.get(video.channel_id)
        if not baseline or not score or score.latest_views is None:
            return None, None, None, None, None
        avg = baseline.get("avg_views")
        med = baseline.get("median_views")
        p75 = baseline.get("p75_views")
        p90 = baseline.get("p90_views")
        latest = score.latest_views

        ratio_avg = round(latest / avg, 1) if avg and avg > 0 else None
        ratio_med = round(latest / med, 1) if med and med > 0 else None

        if p90 is not None and latest >= p90:
            bucket = "top_10_percent"
        elif p75 is not None and latest >= p75:
            bucket = "top_25_percent"
        else:
            bucket = "normal"

        return avg, med, ratio_avg, ratio_med, bucket

    result = []
    for video, channel, score, classification in rows:
        cav, cmv, r2a, r2m, pb = _explain_for(video, score)
        result.append(
            OutlierRead(
                video_id=video.id,
                youtube_video_id=video.youtube_video_id,
                title=video.title,
                channel_title=channel.title,
                channel_subscribers=channel.subscriber_count,
                published_at=video.published_at,
                latest_views=score.latest_views,
                views_per_day=score.views_per_day,
                views_per_sub=score.views_per_sub,
                channel_baseline_vpd=score.channel_baseline_vpd,
                outlier_multiplier=score.outlier_multiplier,
                outlier_score=score.outlier_score,
                repeatability_score=score.repeatability_score,
                is_small_channel_breakout=score.is_small_channel_breakout,
                explanation=score.explanation,
                classification=AIClassificationRead.model_validate(classification) if classification else None,
                thumbnail_url=video.thumbnail_url,
                url=f"https://www.youtube.com/watch?v={video.youtube_video_id}",
                channel_avg_views=cav,
                channel_median_views=cmv,
                ratio_to_avg=r2a,
                ratio_to_median=r2m,
                percentile_bucket=pb,
            )
        )
    return result


def get_niche_coverage(db: Session) -> dict[str, Any]:
    total = db.scalar(select(func.count(Video.id))) or 0
    classified = (
        db.scalar(
            select(func.count(func.distinct(AIClassification.video_id)))
            .where(AIClassification.niche_label.isnot(None))
        )
        or 0
    )
    other = (
        db.scalar(
            select(func.count(func.distinct(AIClassification.video_id)))
            .where(AIClassification.niche_label == "Other")
        )
        or 0
    )
    coverage = round(classified / total * 100, 1) if total > 0 else 0.0
    return {
        "videos_total": total,
        "classified": classified,
        "other": other,
        "coverage_percent": coverage,
    }


def get_niche_detail(
    db: Session, niche: str, period_days: int = 30
) -> dict[str, Any] | None:
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=period_days)

    stats = (
        db.execute(
            select(
                func.count(func.distinct(AIClassification.video_id)).label("videos_count"),
                func.coalesce(func.avg(VideoScore.latest_views), 0).label("avg_views"),
                func.coalesce(func.avg(VideoScore.outlier_score), 0).label("avg_outlier_score"),
            )
            .join(Video, Video.id == AIClassification.video_id)
            .join(VideoScore, VideoScore.video_id == AIClassification.video_id)
            .where(
                AIClassification.niche_label == niche,
                cast(Video.published_at, Date) >= cast(cutoff, Date),
            )
        )
        .one()
    )

    if stats.videos_count == 0:
        return None

    return {
        "niche": niche,
        "videos_count": stats.videos_count,
        "avg_views": round(float(stats.avg_views)),
        "avg_outlier_score": round(float(stats.avg_outlier_score), 2),
    }


def get_niche_trend(
    db: Session, niche: str, period_days: int = 30
) -> float | None:
    growth_data = get_niche_growth(db, period_days)
    counts = growth_data.get(niche)
    if not counts:
        return None
    earlier = counts["earlier"]
    recent = counts["recent"]
    if earlier > 0:
        return round((recent - earlier) / earlier * 100, 1)
    return round(recent * 100, 1) if recent > 0 else 0.0


def get_niche_videos_last_period(
    db: Session, niche: str, days: int
) -> int:
    now = datetime.now(UTC)
    cutoff = now - timedelta(days=days)
    return (
        db.scalar(
            select(func.count(func.distinct(AIClassification.video_id)))
            .join(Video, Video.id == AIClassification.video_id)
            .where(
                AIClassification.niche_label == niche,
                cast(Video.published_at, Date) >= cast(cutoff, Date),
            )
        )
        or 0
    )
