from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from celery import Celery

from app.core.config import settings
from app.db.session import SessionLocal
from app.models import Channel, TaskRun
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
def sync_channel_task(self, task_run_id: int, channel_id: int, limit: int | None = None) -> dict[str, Any]:
    update_task_status(task_run_id, status="running")
    db = SessionLocal()
    try:
        result = sync_channel_videos(db, channel_id, limit=limit, related_task_id=task_run_id)
        channel = db.get(Channel, channel_id)
        result["requested_limit"] = limit or settings.default_sync_limit
        result["channel_title"] = channel.title if channel else None
        result["youtube_channel_id"] = channel.youtube_channel_id if channel else None
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