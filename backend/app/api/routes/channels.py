from __future__ import annotations

from datetime import datetime

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


def _build_scan_options(
    limit: int | None = None,
    min_views: int | None = None,
    max_views: int | None = None,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    min_views_per_day: float | None = None,
    max_views_per_day: float | None = None,
    stop_after_matches: int | None = None,
    save_skipped: bool = True,
) -> dict:
    resolved_limit = _resolve_limit(limit)
    opt: dict = {"limit": resolved_limit, "save_skipped": save_skipped}
    if min_views is not None:
        opt["min_views"] = min_views
    if max_views is not None:
        opt["max_views"] = max_views
    if published_after is not None:
        opt["published_after"] = published_after.isoformat()
    if published_before is not None:
        opt["published_before"] = published_before.isoformat()
    if min_views_per_day is not None:
        opt["min_views_per_day"] = min_views_per_day
    if max_views_per_day is not None:
        opt["max_views_per_day"] = max_views_per_day
    if stop_after_matches is not None:
        opt["stop_after_matches"] = stop_after_matches
    return opt


def _validate_scan_options(
    min_views: int | None = None,
    max_views: int | None = None,
    min_views_per_day: float | None = None,
    max_views_per_day: float | None = None,
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    stop_after_matches: int | None = None,
) -> str | None:
    if min_views is not None and max_views is not None and min_views > max_views:
        return "min_views must not be greater than max_views"
    if min_views_per_day is not None and max_views_per_day is not None and min_views_per_day > max_views_per_day:
        return "min_views_per_day must not be greater than max_views_per_day"
    if published_after is not None and published_before is not None and published_after > published_before:
        return "published_after must not be later than published_before"
    if stop_after_matches is not None and (stop_after_matches < 1 or stop_after_matches > 500):
        return "stop_after_matches must be between 1 and 500"
    return None


def _queue_channel_sync(db: Session, channel_id: int, scan_options: dict | None = None) -> SyncResponse:
    if scan_options is None:
        scan_options = {"limit": _resolve_limit(None), "save_skipped": True}
    task_run = TaskRun(
        task_type="sync_channel",
        status="pending",
        channel_id=channel_id,
        params={"scan_options": scan_options},
    )
    db.add(task_run)
    db.commit()
    db.refresh(task_run)

    task = sync_channel_task.apply_async(args=[task_run.id, channel_id], kwargs={"scan_options": scan_options})
    task_run.provider_task_id = task.id
    db.commit()
    return SyncResponse(
        task_run_id=task_run.id,
        task_id=task.id,
        channel_id=channel_id,
        requested_limit=scan_options.get("limit"),
        scan_options=scan_options,
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
    min_views: int | None = Query(default=None, ge=0),
    max_views: int | None = Query(default=None, ge=0),
    min_views_per_day: float | None = Query(default=None, ge=0),
    max_views_per_day: float | None = Query(default=None, ge=0),
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    stop_after_matches: int | None = Query(default=None, ge=1),
    save_skipped: bool = Query(default=True),
) -> SyncResponse:
    if not db.get(Channel, channel_id):
        raise HTTPException(status_code=404, detail="Channel not found")
    err = _validate_scan_options(
        min_views=min_views, max_views=max_views,
        min_views_per_day=min_views_per_day, max_views_per_day=max_views_per_day,
        published_after=published_after, published_before=published_before,
        stop_after_matches=stop_after_matches,
    )
    if err:
        raise HTTPException(status_code=400, detail=err)
    scan_options = _build_scan_options(
        limit=limit, min_views=min_views, max_views=max_views,
        published_after=published_after, published_before=published_before,
        min_views_per_day=min_views_per_day, max_views_per_day=max_views_per_day,
        stop_after_matches=stop_after_matches, save_skipped=save_skipped,
    )
    return _queue_channel_sync(db, channel_id, scan_options)


@router.post("/sync-all", response_model=SyncAllResponse)
def sync_all_channels(
    db: Session = Depends(get_db),
    limit: int | None = Query(default=None, ge=1, le=500),
    min_views: int | None = Query(default=None, ge=0),
    max_views: int | None = Query(default=None, ge=0),
    min_views_per_day: float | None = Query(default=None, ge=0),
    max_views_per_day: float | None = Query(default=None, ge=0),
    published_after: datetime | None = None,
    published_before: datetime | None = None,
    stop_after_matches: int | None = Query(default=None, ge=1),
    save_skipped: bool = Query(default=True),
    max_channels: int = Query(default=100, ge=1, le=1_000),
) -> SyncAllResponse:
    err = _validate_scan_options(
        min_views=min_views, max_views=max_views,
        min_views_per_day=min_views_per_day, max_views_per_day=max_views_per_day,
        published_after=published_after, published_before=published_before,
        stop_after_matches=stop_after_matches,
    )
    if err:
        raise HTTPException(status_code=400, detail=err)
    scan_options = _build_scan_options(
        limit=limit, min_views=min_views, max_views=max_views,
        published_after=published_after, published_before=published_before,
        min_views_per_day=min_views_per_day, max_views_per_day=max_views_per_day,
        stop_after_matches=stop_after_matches, save_skipped=save_skipped,
    )
    channels = list(
        db.scalars(
            select(Channel).where(Channel.status == "active").order_by(Channel.last_synced_at.asc().nullsfirst()).limit(max_channels)
        ).all()
    )
    tasks = [_queue_channel_sync(db, channel.id, scan_options) for channel in channels]
    return SyncAllResponse(
        queued=len(tasks),
        tasks=tasks,
        requested_limit=scan_options.get("limit"),
        max_channels=max_channels,
        scan_options=scan_options,
    )
