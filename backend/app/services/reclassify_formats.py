from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIClassification, Video
from app.services.format_classifier import classify_video

logger = logging.getLogger(__name__)


def reclassify_all_videos(db: Session) -> dict:
    video_ids = list(db.scalars(select(Video.id)).all())
    total = len(video_ids)
    updated = 0
    failed = 0

    for vid in video_ids:
        try:
            video = db.get(Video, vid)
            if not video:
                continue

            result = classify_video(video.title, video.description, None)

            existing = db.scalar(
                select(AIClassification).where(
                    AIClassification.video_id == video.id,
                    AIClassification.model == "stub",
                    AIClassification.prompt_version == "rule_v1",
                )
            )

            if existing is None:
                existing = AIClassification(
                    video_id=video.id,
                    model="stub",
                    prompt_version="rule_v1",
                )
                db.add(existing)

            existing.format_label = result["format_label"]
            existing.is_faceless_friendly = result["is_faceless_friendly"]
            existing.is_ai_friendly = result["is_ai_friendly"]
            existing.classifier_version = result["classifier_version"]
            db.flush()
            updated += 1
        except Exception as exc:
            logger.warning("Failed to reclassify video %s: %s", vid, exc)
            failed += 1

    db.commit()

    return {
        "videos_processed": total,
        "updated": updated,
        "failed": failed,
    }
