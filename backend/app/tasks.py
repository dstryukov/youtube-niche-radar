from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from celery import Celery
from sqlalchemy import desc, select

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Channel, TaskRun, Video, VideoScore
from app.services.ai_classifier import classify_and_save_video
from app.services.ingest import sync_channel_videos

celery_app = Celery("youtube_niche_radar", broker=settings.redis_url, backend=settings.redis_url)


def update_task_status(
    task_run_id: int,
    *,
    status: str,
    result: dict[str, Any] | None = None,
    error: str | None = None,
) -> None:
    db = SessionLocal()
    try:
        task_run = db.get(TaskRun, task_run_id)
        if not task_run:
            return
        task_run.status = status
        if status == "running":
            task_run.started_at = datetime.now(UTC)
        if status in {"success", "failed"}:
            task_run.finished_at = datetime.now(UTC)
        if result is not None:
            task_run.result = result
        if error is not None:
            task_run.error = error
        db.commit()
    except Exception:
        db.rollback()
    finally:
        db.close()


@celery_app.task(name="sync_channel", bind=True, max_retries=3, default_retry_delay=60)
def sync_channel_task(self, task_run_id: int, channel_id: int, scan_options: dict | None = None) -> dict[str, Any]:
    update_task_status(task_run_id, status="running")
    db = SessionLocal()
    try:
        if scan_options is None:
            scan_options = {"limit": settings.default_sync_limit, "save_skipped": True}
        result = sync_channel_videos(db, channel_id, scan_options=scan_options, related_task_id=task_run_id)
        channel = db.get(Channel, channel_id)
        result["requested_limit"] = scan_options.get("limit", settings.default_sync_limit)
        result["channel_title"] = channel.title if channel else None
        result["youtube_channel_id"] = channel.youtube_channel_id if channel else None
        result["scan_options"] = scan_options
        update_task_status(task_run_id, status="success", result=result)
        return result
    except Exception as exc:
        error_message = str(exc)
        update_task_status(task_run_id, status="failed", error=error_message)
        try:
            raise self.retry(exc=exc)
        except Exception as retry_exc:
            update_task_status(task_run_id, status="failed", error=f"Failed after retries: {retry_exc}")
            raise
    finally:
        db.close()


@celery_app.task(name="classify_outliers", bind=True, max_retries=2)
def classify_outliers_task(
    self,
    min_outlier_score: float = 0.3,
    limit: int = 50,
    provider: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    """Classifies all unclassified anomalies with outlier_score >= min_outlier_score.

    If provider/model are specified, temporarily overrides settings.
    """
    db = SessionLocal()
    try:
        videos = list(
            db.scalars(
                select(Video)
                .join(VideoScore, VideoScore.video_id == Video.id)
                .where(VideoScore.outlier_score >= min_outlier_score)
                .order_by(desc(VideoScore.outlier_score))
                .limit(limit)
            ).all()
        )
        classified = 0
        failed = 0
        for video in videos:
            try:
                classify_and_save_video(db, video, provider=provider, model=model)
                classified += 1
            except Exception:
                failed += 1
        return {"classified": classified, "failed": failed, "total": len(videos)}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()
