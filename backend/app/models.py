from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    pass


class Channel(Base):
    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_channel_id: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    title: Mapped[str | None] = mapped_column(String(512))
    handle: Mapped[str | None] = mapped_column(String(255), index=True)
    uploads_playlist_id: Mapped[str | None] = mapped_column(String(64), index=True)
    subscriber_count: Mapped[int | None] = mapped_column(BigInteger)
    view_count: Mapped[int | None] = mapped_column(BigInteger)
    video_count: Mapped[int | None] = mapped_column(BigInteger)
    country: Mapped[str | None] = mapped_column(String(8))
    status: Mapped[str] = mapped_column(String(32), default="active", index=True)
    source: Mapped[str | None] = mapped_column(String(64), default="manual")
    tags: Mapped[list[str] | None] = mapped_column(JSONB)
    notes: Mapped[str | None] = mapped_column(Text)
    last_synced_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    videos: Mapped[list["Video"]] = relationship(back_populates="channel")
    snapshots: Mapped[list["ChannelSnapshot"]] = relationship(back_populates="channel")


class ChannelSnapshot(Base):
    __tablename__ = "channel_snapshots"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    subscriber_count: Mapped[int | None] = mapped_column(BigInteger)
    view_count: Mapped[int | None] = mapped_column(BigInteger)
    video_count: Mapped[int | None] = mapped_column(BigInteger)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    channel: Mapped[Channel] = relationship(back_populates="snapshots")


class Video(Base):
    __tablename__ = "videos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    youtube_video_id: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    channel_id: Mapped[int] = mapped_column(ForeignKey("channels.id", ondelete="CASCADE"), index=True)
    title: Mapped[str] = mapped_column(String(512))
    description: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    duration_iso8601: Mapped[str | None] = mapped_column(String(64))
    duration_seconds: Mapped[int | None] = mapped_column(Integer, index=True)
    category_id: Mapped[str | None] = mapped_column(String(32))
    thumbnail_url: Mapped[str | None] = mapped_column(Text)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    channel: Mapped[Channel] = relationship(back_populates="videos")
    snapshots: Mapped[list["VideoSnapshot"]] = relationship(back_populates="video")
    score: Mapped["VideoScore | None"] = relationship(back_populates="video")
    classifications: Mapped[list["AIClassification"]] = relationship(back_populates="video")


class VideoSnapshot(Base):
    __tablename__ = "video_snapshots"
    __table_args__ = (UniqueConstraint("video_id", "observed_at", name="uq_video_snapshot_time"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    view_count: Mapped[int | None] = mapped_column(BigInteger)
    like_count: Mapped[int | None] = mapped_column(BigInteger)
    comment_count: Mapped[int | None] = mapped_column(BigInteger)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)

    video: Mapped[Video] = relationship(back_populates="snapshots")


class VideoScore(Base):
    __tablename__ = "video_scores"
    __table_args__ = (UniqueConstraint("video_id", name="uq_video_score_video"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    calculated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), index=True
    )
    age_days: Mapped[float | None] = mapped_column(Float)
    latest_views: Mapped[int | None] = mapped_column(BigInteger)
    views_per_day: Mapped[float | None] = mapped_column(Float, index=True)
    views_per_sub: Mapped[float | None] = mapped_column(Float, index=True)
    channel_baseline_vpd: Mapped[float | None] = mapped_column(Float)
    channel_baseline_views: Mapped[float | None] = mapped_column(Float)
    outlier_multiplier: Mapped[float | None] = mapped_column(Float, index=True)
    outlier_score: Mapped[float | None] = mapped_column(Float, index=True)
    velocity_score: Mapped[float | None] = mapped_column(Float)
    consistency_score: Mapped[float | None] = mapped_column(Float)
    repeatability_score: Mapped[float | None] = mapped_column(Float, index=True)
    is_small_channel_breakout: Mapped[bool] = mapped_column(Boolean, default=False, index=True)
    explanation: Mapped[str | None] = mapped_column(Text)

    video: Mapped[Video] = relationship(back_populates="score")


class Format(Base):
    __tablename__ = "formats"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text)
    is_faceless_friendly: Mapped[bool | None] = mapped_column(Boolean)
    is_ai_friendly: Mapped[bool | None] = mapped_column(Boolean)
    repeatability_prior: Mapped[float | None] = mapped_column(Float)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Niche(Base):
    __tablename__ = "niches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    label: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    parent_label: Mapped[str | None] = mapped_column(String(255), index=True)
    description: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AIClassification(Base):
    __tablename__ = "ai_classifications"
    __table_args__ = (UniqueConstraint("video_id", "model", "prompt_version", name="uq_ai_classification_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    video_id: Mapped[int] = mapped_column(ForeignKey("videos.id", ondelete="CASCADE"), index=True)
    model: Mapped[str] = mapped_column(String(128))
    prompt_version: Mapped[str] = mapped_column(String(64))
    format_id: Mapped[int | None] = mapped_column(ForeignKey("formats.id", ondelete="SET NULL"), index=True)
    niche_id: Mapped[int | None] = mapped_column(ForeignKey("niches.id", ondelete="SET NULL"), index=True)
    format_label: Mapped[str | None] = mapped_column(String(255), index=True)
    niche_label: Mapped[str | None] = mapped_column(String(255), index=True)
    hook_type: Mapped[str | None] = mapped_column(String(255), index=True)
    target_audience: Mapped[str | None] = mapped_column(String(255))
    is_faceless_friendly: Mapped[bool | None] = mapped_column(Boolean, index=True)
    is_ai_friendly: Mapped[bool | None] = mapped_column(Boolean, index=True)
    repeatability_score: Mapped[float | None] = mapped_column(Float, index=True)
    adaptation_ideas: Mapped[list[str] | None] = mapped_column(JSONB)
    confidence: Mapped[float | None] = mapped_column(Float)
    rationale: Mapped[str | None] = mapped_column(Text)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    video: Mapped[Video] = relationship(back_populates="classifications")


class TaskRun(Base):
    __tablename__ = "task_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider_task_id: Mapped[str | None] = mapped_column(String(128), unique=True, index=True)
    task_type: Mapped[str] = mapped_column(String(64), index=True)
    status: Mapped[str] = mapped_column(String(32), default="pending", index=True)
    channel_id: Mapped[int | None] = mapped_column(ForeignKey("channels.id", ondelete="SET NULL"), index=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    params: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    result: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
    error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class ApiQuotaUsage(Base):
    __tablename__ = "api_quota_usage"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    provider: Mapped[str] = mapped_column(String(64), index=True)
    endpoint: Mapped[str] = mapped_column(String(128), index=True)
    units: Mapped[int] = mapped_column(Integer)
    request_count: Mapped[int] = mapped_column(Integer, default=1)
    related_task_id: Mapped[int | None] = mapped_column(ForeignKey("task_runs.id", ondelete="SET NULL"))
    observed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)
    raw: Mapped[dict[str, Any] | None] = mapped_column(JSONB)
