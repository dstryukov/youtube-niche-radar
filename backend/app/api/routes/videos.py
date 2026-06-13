from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AIClassification, Channel, Video, VideoScore
from app.schemas import AIClassificationRead, OutlierRead
from app.services.ai_classifier import classify_and_save_video
from app.services.channel_baseline import compute_channel_baseline
from app.services.outlier_explainer import explain_video

router = APIRouter(prefix="/videos", tags=["videos"])

VALID_SORTS = {"outlier_score", "views_per_day", "published_at", "outlier_multiplier", "latest_views"}


def _latest_classification_subquery():
    return (
        select(
            AIClassification.video_id,
            AIClassification.id.label("classification_id"),
        )
        .distinct(AIClassification.video_id)
        .order_by(AIClassification.video_id, AIClassification.created_at.desc())
        .subquery()
    )


def _sort_clause(sort: str):
    mapping = {
        "outlier_score": desc(VideoScore.outlier_score),
        "views_per_day": desc(VideoScore.views_per_day),
        "published_at": desc(Video.published_at),
        "outlier_multiplier": desc(VideoScore.outlier_multiplier),
        "latest_views": desc(VideoScore.latest_views),
    }
    return mapping[sort]


@router.get("/outliers", response_model=list[OutlierRead])
def list_outliers(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
    min_outlier_score: float | None = None,
    small_channel_breakout: bool | None = None,
    format_label: str | None = None,
    niche_label: str | None = None,
    is_faceless_friendly: bool | None = None,
    is_ai_friendly: bool | None = None,
    sort: str = Query(default="outlier_score"),
    min_views: int | None = None,
    max_views: int | None = None,
    min_views_per_day: float | None = None,
    max_views_per_day: float | None = None,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
) -> list[OutlierRead]:
    if sort not in VALID_SORTS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid sort value '{sort}'. Allowed: {', '.join(sorted(VALID_SORTS))}",
        )
    if min_views is not None and max_views is not None and min_views > max_views:
        raise HTTPException(status_code=400, detail="min_views must not be greater than max_views")
    if min_views_per_day is not None and max_views_per_day is not None and min_views_per_day > max_views_per_day:
        raise HTTPException(status_code=400, detail="min_views_per_day must not be greater than max_views_per_day")
    if published_after is not None and published_before is not None and published_after > published_before:
        raise HTTPException(status_code=400, detail="published_after must not be later than published_before")

    latest_class = _latest_classification_subquery()
    stmt = (
        select(Video, Channel, VideoScore, AIClassification)
        .join(Channel, Channel.id == Video.channel_id)
        .join(VideoScore, VideoScore.video_id == Video.id)
        .outerjoin(latest_class, latest_class.c.video_id == Video.id)
        .outerjoin(AIClassification, AIClassification.id == latest_class.c.classification_id)
        .order_by(_sort_clause(sort), desc(VideoScore.views_per_day))
        .limit(limit)
    )
    if min_outlier_score is not None:
        stmt = stmt.where(VideoScore.outlier_score >= min_outlier_score)
    if small_channel_breakout:
        stmt = stmt.where(VideoScore.is_small_channel_breakout.is_(True))
    if format_label:
        stmt = stmt.where(AIClassification.format_label == format_label)
    if niche_label:
        stmt = stmt.where(AIClassification.niche_label == niche_label)
    if is_faceless_friendly is not None:
        stmt = stmt.where(AIClassification.is_faceless_friendly.is_(is_faceless_friendly))
    if is_ai_friendly is not None:
        stmt = stmt.where(AIClassification.is_ai_friendly.is_(is_ai_friendly))
    if min_views is not None:
        stmt = stmt.where(VideoScore.latest_views >= min_views)
    if max_views is not None:
        stmt = stmt.where(VideoScore.latest_views <= max_views)
    if min_views_per_day is not None:
        stmt = stmt.where(VideoScore.views_per_day >= min_views_per_day)
    if max_views_per_day is not None:
        stmt = stmt.where(VideoScore.views_per_day <= max_views_per_day)
    if published_after is not None:
        stmt = stmt.where(Video.published_at >= published_after)
    if published_before is not None:
        stmt = stmt.where(Video.published_at <= published_before)

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


@router.post("/{video_id}/classify", response_model=AIClassificationRead)
def classify_video(video_id: int, db: Session = Depends(get_db)) -> AIClassification:
    video = db.get(Video, video_id)
    if not video:
        raise HTTPException(status_code=404, detail="Video not found")
    return classify_and_save_video(db, video)


@router.post("/classify-outliers", response_model=list[AIClassificationRead])
def classify_outliers(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
    min_outlier_score: float = Query(default=0.3),
    provider: str | None = Query(default=None, description="groq | gemini"),
    model: str | None = Query(default=None, description="Override LLM model"),
) -> list[AIClassification]:
    videos = list(
        db.scalars(
            select(Video)
            .join(VideoScore, VideoScore.video_id == Video.id)
            .where(VideoScore.outlier_score >= min_outlier_score)
            .order_by(desc(VideoScore.outlier_score))
            .limit(limit)
        ).all()
    )
    return [classify_and_save_video(db, video, provider=provider, model=model) for video in videos]
