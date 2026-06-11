from __future__ import annotations

import csv
from datetime import UTC, datetime
from io import StringIO
from typing import Any

from dateutil.parser import isoparse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Channel, ChannelSnapshot, Video, VideoSnapshot
from app.services.metrics import calculate_video_score
from app.services.quota import log_quota_usage
from app.utils import extract_channel_ref, parse_iso8601_duration_seconds
from app.youtube.client import YouTubeClient


def _int_or_none(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _best_thumbnail(snippet: dict[str, Any]) -> str | None:
    thumbnails = snippet.get("thumbnails", {}) or {}
    for key in ("maxres", "standard", "high", "medium", "default"):
        if key in thumbnails and thumbnails[key].get("url"):
            return thumbnails[key]["url"]
    return None


def upsert_channel_from_youtube(
    db: Session,
    *,
    channel_id: str | None = None,
    handle: str | None = None,
    source: str | None = None,
    tags: list[str] | None = None,
    notes: str | None = None,
    related_task_id: int | None = None,
) -> Channel:
    yt = YouTubeClient()
    item = yt.get_channel(channel_id=channel_id, handle=handle)
    log_quota_usage(db, endpoint="channels", related_task_id=related_task_id)

    snippet = item.get("snippet", {})
    statistics = item.get("statistics", {})
    content_details = item.get("contentDetails", {})
    related_playlists = content_details.get("relatedPlaylists", {})

    youtube_channel_id = item["id"]
    channel = db.scalar(select(Channel).where(Channel.youtube_channel_id == youtube_channel_id))
    if channel is None:
        channel = Channel(youtube_channel_id=youtube_channel_id)
        db.add(channel)

    channel.title = snippet.get("title")
    channel.handle = snippet.get("customUrl") or handle
    channel.uploads_playlist_id = related_playlists.get("uploads")
    channel.subscriber_count = _int_or_none(statistics.get("subscriberCount"))
    channel.view_count = _int_or_none(statistics.get("viewCount"))
    channel.video_count = _int_or_none(statistics.get("videoCount"))
    channel.country = snippet.get("country")
    channel.source = source or channel.source or "manual"
    if tags is not None:
        channel.tags = tags
    if notes is not None:
        channel.notes = notes
    channel.last_synced_at = datetime.now(UTC)

    db.flush()
    db.add(
        ChannelSnapshot(
            channel_id=channel.id,
            subscriber_count=channel.subscriber_count,
            view_count=channel.view_count,
            video_count=channel.video_count,
            raw=item,
        )
    )
    db.commit()
    db.refresh(channel)
    return channel


def sync_channel_videos(
    db: Session,
    channel_db_id: int,
    *,
    limit: int | None = None,
    related_task_id: int | None = None,
) -> dict[str, int]:
    limit = limit or settings.sync_recent_video_limit
    channel = db.get(Channel, channel_db_id)
    if channel is None:
        raise ValueError("Channel not found")

    # Refresh channel metadata first, so subscriber_count and uploads_playlist_id are fresh.
    channel = upsert_channel_from_youtube(
        db, channel_id=channel.youtube_channel_id, related_task_id=related_task_id
    )
    if not channel.uploads_playlist_id:
        raise ValueError("Channel has no uploads playlist")

    yt = YouTubeClient()
    video_ids, playlist_requests = yt.list_upload_playlist_video_ids_with_request_count(
        channel.uploads_playlist_id, limit=limit
    )
    log_quota_usage(
        db,
        endpoint="playlistItems",
        request_count=playlist_requests,
        related_task_id=related_task_id,
    )
    video_items, video_requests = yt.get_videos_with_request_count(video_ids)
    log_quota_usage(db, endpoint="videos", request_count=video_requests, related_task_id=related_task_id)

    upserted = 0
    updated = 0
    snapshots = 0
    for item in video_items:
        snippet = item.get("snippet", {})
        statistics = item.get("statistics", {})
        content_details = item.get("contentDetails", {})

        youtube_video_id = item["id"]
        video = db.scalar(select(Video).where(Video.youtube_video_id == youtube_video_id))
        if video is None:
            video = Video(
                youtube_video_id=youtube_video_id,
                channel_id=channel.id,
                title=snippet.get("title") or "",
            )
            db.add(video)
            upserted += 1
        else:
            updated += 1

        duration_iso = content_details.get("duration")
        video.channel_id = channel.id
        video.title = snippet.get("title") or ""
        video.description = snippet.get("description")
        video.published_at = isoparse(snippet["publishedAt"])
        video.duration_iso8601 = duration_iso
        video.duration_seconds = parse_iso8601_duration_seconds(duration_iso)
        video.category_id = snippet.get("categoryId")
        video.thumbnail_url = _best_thumbnail(snippet)
        video.raw = item
        db.flush()

        db.add(
            VideoSnapshot(
                video_id=video.id,
                view_count=_int_or_none(statistics.get("viewCount")),
                like_count=_int_or_none(statistics.get("likeCount")),
                comment_count=_int_or_none(statistics.get("commentCount")),
                raw=statistics,
            )
        )
        snapshots += 1
        calculate_video_score(db, video)

    db.commit()
    return {
        "videos_found": len(video_ids),
        "videos_upserted": upserted,
        "videos_updated": updated,
        "snapshots_created": snapshots,
        "youtube_quota_units": 1 + playlist_requests + video_requests,
    }


def import_channels_from_csv(db: Session, csv_text: str) -> dict[str, Any]:
    """Import channels from CSV with columns: channel_id, handle, url, tags, notes.

    A single-column CSV is also supported; each value may be a channel id, handle, or YouTube URL.
    Empty rows are silently skipped and not counted in total_rows.
    Malformed rows are reported in the errors list.
    """
    reader = csv.DictReader(StringIO(csv_text))
    rows: list[dict[str, str]]
    if reader.fieldnames and len(reader.fieldnames) == 1 and reader.fieldnames[0] not in {
        "channel_id",
        "handle",
        "url",
    }:
        # csv.DictReader treats the first plain value as the header. Re-parse as a single-column file.
        values = [line.strip() for line in csv_text.splitlines() if line.strip()]
        rows = [{"value": value} for value in values]
    else:
        rows = list(reader)

    imported: list[Channel] = []
    errors: list[dict[str, Any]] = []
    skipped = 0
    total_raw = 0

    for idx, row in enumerate(rows, start=1):
        raw_ref = (row.get("channel_id") or row.get("handle") or row.get("url") or row.get("value") or "").strip()
        # Skip completely empty rows
        if not raw_ref:
            skipped += 1
            continue
        total_raw += 1

        channel_id, handle = extract_channel_ref(raw_ref)
        if not channel_id and not handle:
            skipped += 1
            errors.append({"row": idx, "value": raw_ref, "error": "Cannot parse channel reference"})
            continue

        try:
            raw_tags = row.get("tags") or ""
            tags = [tag.strip() for tag in raw_tags.split(";") if tag.strip()] or None
            imported.append(
                upsert_channel_from_youtube(
                    db,
                    channel_id=channel_id,
                    handle=handle,
                    source="csv",
                    tags=tags,
                    notes=row.get("notes"),
                )
            )
        except Exception as exc:  # noqa: BLE001 - importing should return row-level errors.
            skipped += 1
            errors.append({"row": idx, "value": raw_ref, "error": str(exc)})

    return {
        "total_rows": total_raw,
        "imported": len(imported),
        "skipped": skipped,
        "errors": errors,
        "channels": imported,
    }
