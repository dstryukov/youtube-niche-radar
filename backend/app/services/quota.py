from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import ApiQuotaUsage

YOUTUBE_ENDPOINT_UNITS = {
    "channels": 1,
    "playlistItems": 1,
    "videos": 1,
    "search": 100,
}


def log_quota_usage(
    db: Session,
    *,
    endpoint: str,
    request_count: int = 1,
    related_task_id: int | None = None,
    raw: dict | None = None,
) -> None:
    units_per_request = YOUTUBE_ENDPOINT_UNITS.get(endpoint, 1)
    db.add(
        ApiQuotaUsage(
            provider="youtube",
            endpoint=endpoint,
            request_count=request_count,
            units=units_per_request * request_count,
            related_task_id=related_task_id,
            raw=raw,
        )
    )
    db.flush()


def youtube_units_used_today(db: Session) -> int:
    result = db.scalar(
        select(func.coalesce(func.sum(ApiQuotaUsage.units), 0)).where(
            ApiQuotaUsage.provider == "youtube",
            func.date(ApiQuotaUsage.observed_at) == func.current_date(),
        )
    )
    return int(result or 0)
