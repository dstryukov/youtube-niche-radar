from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.reclassify_formats import reclassify_all_videos
from app.services.reclassify_niches import reclassify_all_niches

router = APIRouter(prefix="/maintenance", tags=["maintenance"])


@router.post("/reclassify-formats")
def reclassify_formats_endpoint(db: Session = Depends(get_db)) -> dict:
    return reclassify_all_videos(db)


@router.post("/reclassify-niches")
def reclassify_niches_endpoint(db: Session = Depends(get_db)) -> dict:
    return reclassify_all_niches(db)
