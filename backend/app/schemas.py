from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ChannelCreate(BaseModel):
    channel_id: str | None = Field(default=None, description="YouTube channel id, e.g. UC...")
    handle: str | None = Field(default=None, description="YouTube handle, e.g. @GoogleDevelopers")
    source: str | None = Field(default="manual", description="manual, csv, seed, competitor, etc.")
    tags: list[str] | None = None
    notes: str | None = None


class ChannelRead(BaseModel):
    id: int
    youtube_channel_id: str
    title: str | None = None
    handle: str | None = None
    uploads_playlist_id: str | None = None
    subscriber_count: int | None = None
    view_count: int | None = None
    video_count: int | None = None
    country: str | None = None
    source: str | None = None
    tags: list[str] | None = None
    last_synced_at: datetime | None = None

    model_config = {"from_attributes": True}


class ChannelImportResult(BaseModel):
    total_rows: int
    imported: int
    skipped: int
    errors: list[dict[str, Any]]
    channels: list[ChannelRead]


class SyncResponse(BaseModel):
    task_run_id: int
    task_id: str
    channel_id: int
    status: str = "pending"
    requested_limit: int | None = None
    scan_options: dict[str, Any] | None = None


class SyncAllResponse(BaseModel):
    queued: int
    tasks: list[SyncResponse]
    requested_limit: int | None = None
    max_channels: int | None = None
    scan_options: dict[str, Any] | None = None


class TaskRunRead(BaseModel):
    id: int
    provider_task_id: str | None = None
    task_type: str
    status: str
    channel_id: int | None = None
    started_at: datetime | None = None
    finished_at: datetime | None = None
    params: dict[str, Any] | None = None
    result: dict[str, Any] | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime | None = None

    model_config = {"from_attributes": True}


class AIClassificationRead(BaseModel):
    format_label: str | None = None
    niche_label: str | None = None
    hook_type: str | None = None
    target_audience: str | None = None
    is_faceless_friendly: bool | None = None
    is_ai_friendly: bool | None = None
    classifier_version: str | None = None
    repeatability_score: float | None = None
    adaptation_ideas: list[str] | None = None
    confidence: float | None = None
    rationale: str | None = None
    model: str | None = None

    model_config = {"from_attributes": True}


class OutlierRead(BaseModel):
    video_id: int
    youtube_video_id: str
    title: str
    channel_title: str | None = None
    channel_subscribers: int | None = None
    published_at: datetime
    latest_views: int | None = None
    views_per_day: float | None = None
    views_per_sub: float | None = None
    channel_baseline_vpd: float | None = None
    outlier_multiplier: float | None = None
    outlier_score: float | None = None
    repeatability_score: float | None = None
    is_small_channel_breakout: bool
    explanation: str | None = None
    classification: AIClassificationRead | None = None
    thumbnail_url: str | None = None
    url: str
    channel_avg_views: int | None = None
    channel_median_views: int | None = None
    ratio_to_avg: float | None = None
    ratio_to_median: float | None = None
    percentile_bucket: str | None = None


class DashboardSummary(BaseModel):
    channels_count: int
    videos_count: int
    small_channel_breakouts_count: int
    avg_outlier_score: float | None = None
    top_formats: list[dict[str, Any]]
    top_niches: list[dict[str, Any]]
    recent_tasks: list[TaskRunRead]
