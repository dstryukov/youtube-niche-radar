from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy import desc, func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AIClassification, Video, VideoScore

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/formats")
def format_statistics(db: Session = Depends(get_db)) -> list[dict]:
    stmt = (
        select(
            AIClassification.format_label,
            func.count(AIClassification.id).label("videos"),
            func.avg(VideoScore.outlier_score).label("avg_outlier_score"),
            func.avg(VideoScore.latest_views).label("avg_views"),
        )
        .join(Video, Video.id == AIClassification.video_id)
        .join(VideoScore, VideoScore.video_id == Video.id)
        .where(
            AIClassification.model == "rule_v1",
            AIClassification.format_label.isnot(None),
        )
        .group_by(AIClassification.format_label)
        .order_by(desc("videos"))
    )

    rows = db.execute(stmt).all()
    return [
        {
            "format_label": row.format_label,
            "videos": row.videos,
            "avg_outlier_score": round(row.avg_outlier_score, 2) if row.avg_outlier_score is not None else None,
            "avg_views": round(row.avg_views) if row.avg_views is not None else None,
        }
        for row in rows
    ]
