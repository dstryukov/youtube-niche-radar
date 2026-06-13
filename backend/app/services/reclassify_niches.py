from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIClassification, Video
from app.services.niche_classifier import NICHE_CLASSIFIER_VERSION, classify_niche

logger = logging.getLogger(__name__)


def reclassify_all_niches(db: Session) -> dict:
    video_ids = list(db.scalars(select(Video.id)).all())
    total = len(video_ids)
    updated = 0
    failed = 0

    for vid in video_ids:
        try:
            video = db.get(Video, vid)
            if not video:
                continue

            channel_title = video.channel.title if video.channel else None

            existing = db.scalar(
                select(AIClassification).where(
                    AIClassification.video_id == video.id,
                    AIClassification.model == NICHE_CLASSIFIER_VERSION,
                    AIClassification.prompt_version == "v1",
                )
            )

            format_label = existing.format_label if existing else None

            result = classify_niche(video.title, video.description, channel_title, format_label)

            if existing is None:
                existing = AIClassification(
                    video_id=video.id,
                    model=NICHE_CLASSIFIER_VERSION,
                    prompt_version="v1",
                )
                db.add(existing)

            existing.niche_label = result["niche_label"]
            existing.classifier_version = result["classifier_version"]
            db.flush()
            updated += 1
        except Exception as exc:
            logger.warning("Failed to reclassify niche for video %s: %s", vid, exc)
            failed += 1

    db.commit()

    return {
        "videos_processed": total,
        "updated": updated,
        "failed": failed,
    }
