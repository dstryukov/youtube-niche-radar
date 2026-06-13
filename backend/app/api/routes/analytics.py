from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models import AIClassification, Video
from app.schemas import OutlierRead
from app.services.format_analytics import get_format_catalog, get_format_details, get_trending_formats
from app.services.niche_analytics import (
    get_niche_catalog,
    get_niche_coverage,
    get_niche_outliers,
    get_niche_videos_last_period,
    get_trending_niches,
)

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


@router.get("/niches")
def niche_catalog(db: Session = Depends(get_db)) -> list[dict]:
    catalog = get_niche_catalog(db)
    for item in catalog:
        niche = item["niche"]
        videos_last_7 = get_niche_videos_last_period(db, niche, 7)
        videos_last_30 = get_niche_videos_last_period(db, niche, 30)
        avg_weekly = videos_last_30 / 4.0 if videos_last_30 > 0 else 0
        growth_rate = round(videos_last_7 / avg_weekly * 100, 1) if avg_weekly > 0 else 0.0
        item["growth_rate"] = growth_rate
        item["videos_last_7_days"] = videos_last_7
        item["videos_last_30_days"] = videos_last_30
    return catalog


@router.get("/niches/trending")
def trending_niches(
    db: Session = Depends(get_db),
    period_days: int = Query(default=30, ge=7, le=365),
) -> list[dict]:
    return get_trending_niches(db, period_days)


@router.get("/niches/coverage")
def niche_coverage(db: Session = Depends(get_db)) -> dict:
    return get_niche_coverage(db)


@router.get("/niches/{niche}/outliers", response_model=list[OutlierRead])
def niche_outliers(
    niche: str,
    db: Session = Depends(get_db),
    limit: int = Query(default=20, ge=1, le=100),
) -> list[OutlierRead]:
    return get_niche_outliers(db, niche, limit)


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
