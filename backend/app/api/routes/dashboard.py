from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AIClassification, Channel, TaskRun, Video, VideoScore
from app.schemas import DashboardSummary

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(db: Session = Depends(get_db)) -> DashboardSummary:
    channels_count = int(db.scalar(select(func.count(Channel.id))) or 0)
    videos_count = int(db.scalar(select(func.count(Video.id))) or 0)
    breakout_count = int(
        db.scalar(select(func.count(VideoScore.id)).where(VideoScore.is_small_channel_breakout.is_(True))) or 0
    )
    avg_outlier_score = db.scalar(select(func.avg(VideoScore.outlier_score)))

    format_count = func.count(AIClassification.id).label("count")
    top_formats_rows = db.execute(
        select(AIClassification.format_label, format_count)
        .where(AIClassification.format_label.is_not(None))
        .group_by(AIClassification.format_label)
        .order_by(desc(format_count))
        .limit(10)
    ).all()

    niche_count = func.count(AIClassification.id).label("count")
    top_niches_rows = db.execute(
        select(AIClassification.niche_label, niche_count)
        .where(AIClassification.niche_label.is_not(None))
        .group_by(AIClassification.niche_label)
        .order_by(desc(niche_count))
        .limit(10)
    ).all()
    recent_tasks = list(db.scalars(select(TaskRun).order_by(TaskRun.created_at.desc()).limit(10)).all())

    return DashboardSummary(
        channels_count=channels_count,
        videos_count=videos_count,
        small_channel_breakouts_count=breakout_count,
        avg_outlier_score=float(avg_outlier_score) if avg_outlier_score is not None else None,
        top_formats=[{"label": label, "count": count} for label, count in top_formats_rows],
        top_niches=[{"label": label, "count": count} for label, count in top_niches_rows],
        recent_tasks=recent_tasks,
    )
