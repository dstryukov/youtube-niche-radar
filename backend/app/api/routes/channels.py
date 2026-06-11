from __future__ import annotations

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.db.session import get_db
from app.models import Channel, TaskRun
from app.schemas import ChannelCreate, ChannelImportResult, ChannelRead, SyncAllResponse, SyncResponse
from app.services.ingest import import_channels_from_csv, upsert_channel_from_youtube
from app.tasks import sync_channel_task

router = APIRouter(prefix="/channels", tags=["channels"])


def _resolve_limit(limit: int | None) -> int:
    return limit if limit is not None else settings.default_sync_limit


def _queue_channel_sync(db: Session, channel_id: int, limit: int | None = None) -> SyncResponse:
    resolved = _resolve_limit(limit)
    task_run = TaskRun(
        task_type="sync_channel",
        status="pending",
        channel_id=channel_id,
        params={"limit": resolved},
    )
    db.add(task_run)
    db.commit()
    db.refresh(task_run)

    task = sync_channel_task.apply_async(args=[task_run.id, channel_id, limit])
    task_run.provider_task_id = task.id
    db.commit()
    return SyncResponse(
        task_run_id=task_run.id,
        task_id=task.id,
        channel_id=channel_id,
        requested_limit=resolved,
    )


@router.post("", response_model=ChannelRead)
def create_channel(payload: ChannelCreate, db: Session = Depends(get_db)) -> Channel:
    if not payload.channel_id and not payload.handle:
        raise HTTPException(status_code=400, detail="channel_id or handle is required")
    try:
        return upsert_channel_from_youtube(
            db,
            channel_id=payload.channel_id,
            handle=payload.handle,
            source=payload.source,
            tags=payload.tags,
            notes=payload.notes,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@router.post("/import-csv", response_model=ChannelImportResult)
async def import_csv(file: UploadFile = File(...), db: Session = Depends(get_db)) -> dict:
    raw = await file.read()
    try:
        csv_text = raw.decode("utf-8-sig")
    except UnicodeDecodeError as exc:
        raise HTTPException(status_code=400, detail="CSV must be UTF-8 encoded") from exc
    return import_channels_from_csv(db, csv_text)


@router.get("", response_model=list[ChannelRead])
def list_channels(
    db: Session = Depends(get_db),
    status: str | None = None,
    limit: int = Query(default=200, ge=1, le=1_000),
) -> list[Channel]:
    stmt = select(Channel).order_by(Channel.created_at.desc()).limit(limit)
    if status:
        stmt = stmt.where(Channel.status == status)
    return list(db.scalars(stmt).all())


@router.post("/{channel_id}/sync", response_model=SyncResponse)
def sync_channel(
    channel_id: int,
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, ge=1, le=500),
) -> SyncResponse:
    if not db.get(Channel, channel_id):
        raise HTTPException(status_code=404, detail="Channel not found")
    return _queue_channel_sync(db, channel_id, limit)


@router.post("/sync-all", response_model=SyncAllResponse)
def sync_all_channels(
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, ge=1, le=500),
    max_channels: int = Query(default=100, ge=1, le=1_000),
) -> SyncAllResponse:
    resolved = _resolve_limit(limit)
    channels = list(
        db.scalars(
            select(Channel).where(Channel.status == "active").order_by(Channel.last_synced_at.asc().nullsfirst()).limit(max_channels)
        ).all()
    )
    tasks = [_queue_channel_sync(db, channel.id, limit) for channel in channels]
    return SyncAllResponse(
        queued=len(tasks),
        tasks=tasks,
        requested_limit=resolved,
        max_channels=max_channels,
    )
