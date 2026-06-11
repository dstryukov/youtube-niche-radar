from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AIClassification, Channel, Video, VideoScore
from app.schemas import AIClassificationRead, OutlierRead
from app.services.ai_classifier import classify_and_save_video

router = APIRouter(prefix="/videos", tags=["videos"])


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


@router.get("/outliers", response_model=list[OutlierRead])
def list_outliers(
    db: Session = Depends(get_db),
    limit: int = Query(default=50, ge=1, le=500),
    min_outlier_score: float | None = None,
    small_channel_only: bool = False,
    format_label: str | None = None,
    niche_label: str | None = None,
) -> list[OutlierRead]:
    latest_class = _latest_classification_subquery()
    stmt = (
        select(Video, Channel, VideoScore, AIClassification)
        .join(Channel, Channel.id == Video.channel_id)
        .join(VideoScore, VideoScore.video_id == Video.id)
        .outerjoin(latest_class, latest_class.c.video_id == Video.id)
        .outerjoin(AIClassification, AIClassification.id == latest_class.c.classification_id)
        .order_by(desc(VideoScore.outlier_score), desc(VideoScore.views_per_day))
        .limit(limit)
    )
    if min_outlier_score is not None:
        stmt = stmt.where(VideoScore.outlier_score >= min_outlier_score)
    if small_channel_only:
        stmt = stmt.where(VideoScore.is_small_channel_breakout.is_(True))
    if format_label:
        stmt = stmt.where(AIClassification.format_label == format_label)
    if niche_label:
        stmt = stmt.where(AIClassification.niche_label == niche_label)

    rows = db.execute(stmt).all()

    return [
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
        )
        for video, channel, score, classification in rows
    ]


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
    return [classify_and_save_video(db, video) for video in videos]
