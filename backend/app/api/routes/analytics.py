from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AIClassification, Video
from app.services.format_analytics import get_format_catalog, get_format_details, get_trending_formats

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/formats")
def format_catalog(db: Session = Depends(get_db)) -> list[dict]:
    return get_format_catalog(db)


@router.get("/formats/trending")
def trending_formats(
    db: Session = Depends(get_db),
    period_days: int = Query(default=30, ge=7, le=365),
) -> list[dict]:
    return get_trending_formats(db, period_days)


@router.get("/formats/coverage")
def format_coverage(db: Session = Depends(get_db)) -> dict:
    total = db.scalar(select(func.count(Video.id))) or 0
    classified = (
        db.scalar(
            select(func.count(func.distinct(AIClassification.video_id)))
            .where(AIClassification.format_label.isnot(None))
        )
        or 0
    )
    other = total - classified
    coverage = round(classified / total * 100, 1) if total > 0 else 0.0
    return {
        "videos_total": total,
        "classified": classified,
        "other": other,
        "coverage_percent": coverage,
    }


@router.get("/formats/{label:path}")
def format_detail(
    label: str,
    db: Session = Depends(get_db),
    period_days: int = Query(default=30, ge=1, le=365),
) -> dict:
    result = get_format_details(db, label, period_days)
    if not result:
        raise HTTPException(status_code=404, detail=f"Format '{label}' not found")
    return result
