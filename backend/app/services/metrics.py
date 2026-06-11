from __future__ import annotations

import math
from datetime import UTC, datetime
from statistics import median

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIClassification, Channel, Video, VideoScore, VideoSnapshot


def _latest_snapshot(db: Session, video_id: int) -> VideoSnapshot | None:
    return db.scalar(
        select(VideoSnapshot)
        .where(VideoSnapshot.video_id == video_id)
        .order_by(VideoSnapshot.observed_at.desc())
        .limit(1)
    )


def _safe_ratio(numerator: float | None, denominator: float | None) -> float | None:
    if numerator is None or denominator is None or denominator <= 0:
        return None
    return numerator / denominator


def calculate_video_score(db: Session, video: Video) -> VideoScore | None:
    snapshot = _latest_snapshot(db, video.id)
    channel = db.get(Channel, video.channel_id)
    if not snapshot or snapshot.view_count is None or not channel:
        return None

    now = datetime.now(UTC)
    age_days = max((now - video.published_at).total_seconds() / 86400, 0.25)
    views_per_day = snapshot.view_count / age_days
    views_per_sub = _safe_ratio(snapshot.view_count, channel.subscriber_count)

    # Baseline: previous 30 videos on this channel, excluding the current video.
    previous_videos = db.scalars(
        select(Video)
        .where(Video.channel_id == video.channel_id, Video.id != video.id, Video.published_at < video.published_at)
        .order_by(Video.published_at.desc())
        .limit(30)
    ).all()

    baseline_vpd_values: list[float] = []
    baseline_view_values: list[int] = []
    for prev in previous_videos:
        prev_snapshot = _latest_snapshot(db, prev.id)
        if prev_snapshot and prev_snapshot.view_count is not None:
            prev_age_days = max((now - prev.published_at).total_seconds() / 86400, 0.25)
            baseline_vpd_values.append(prev_snapshot.view_count / prev_age_days)
            baseline_view_values.append(prev_snapshot.view_count)

    channel_baseline_vpd = median(baseline_vpd_values) if baseline_vpd_values else None
    channel_baseline_views = median(baseline_view_values) if baseline_view_values else None

    if channel_baseline_vpd and channel_baseline_vpd > 0:
        outlier_multiplier = (views_per_day + 1) / (channel_baseline_vpd + 1)
        outlier_score = math.log10(outlier_multiplier)
    else:
        # Cold-start fallback. It is intentionally conservative and should be replaced after a channel has history.
        outlier_multiplier = None
        outlier_score = min(math.log10(views_per_day + 1) / 4, 1.5)

    velocity_score = min(math.log10(views_per_day + 1) / 5, 1.0)

    # Consistency penalty: a format is less interesting when the channel has too little baseline.
    consistency_score = min(len(baseline_vpd_values) / 10, 1.0)

    latest_classification = db.scalar(
        select(AIClassification)
        .where(AIClassification.video_id == video.id)
        .order_by(AIClassification.created_at.desc())
        .limit(1)
    )
    repeatability_score = latest_classification.repeatability_score if latest_classification else None

    is_small_channel_breakout = bool(
        channel.subscriber_count
        and channel.subscriber_count <= 100_000
        and snapshot.view_count >= max(50_000, 2.0 * channel.subscriber_count)
    )

    if outlier_multiplier:
        explanation = (
            f"Видео набирает примерно x{outlier_multiplier:.1f} к медианной скорости канала "
            f"({views_per_day:,.0f} views/day против baseline {channel_baseline_vpd:,.0f})."
        )
    else:
        explanation = (
            "У канала пока мало истории для честного baseline; скоринг основан на абсолютной скорости просмотров."
        )

    score = db.scalar(select(VideoScore).where(VideoScore.video_id == video.id))
    if score is None:
        score = VideoScore(video_id=video.id)
        db.add(score)

    score.calculated_at = now
    score.age_days = age_days
    score.latest_views = snapshot.view_count
    score.views_per_day = views_per_day
    score.views_per_sub = views_per_sub
    score.channel_baseline_vpd = channel_baseline_vpd
    score.channel_baseline_views = channel_baseline_views
    score.outlier_multiplier = outlier_multiplier
    score.outlier_score = outlier_score
    score.velocity_score = velocity_score
    score.consistency_score = consistency_score
    score.repeatability_score = repeatability_score
    score.is_small_channel_breakout = is_small_channel_breakout
    score.explanation = explanation
    db.flush()
    return score
