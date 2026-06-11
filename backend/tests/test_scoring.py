from __future__ import annotations

import math
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock

from sqlalchemy.orm import Session

from app.models import Channel, Video, VideoScore, VideoSnapshot
from app.services.metrics import calculate_video_score


def _make_mock_db(
    *,
    channel: Channel | None = None,
    snapshot: VideoSnapshot | None = None,
    previous_videos: list[Video] = None,
    existing_score: VideoScore | None = None,
) -> MagicMock:
    db = MagicMock(spec=Session)

    def mock_get(model, ident):
        if model == Channel and channel and ident == channel.id:
            return channel
        return None

    db.get = mock_get
    db.add = MagicMock()
    db.flush = MagicMock()

    # scalar is called for: current _latest_snapshot, each prev _latest_snapshot, AIClassification, then existing VideoScore
    n_prev = len(previous_videos) if previous_videos else 0
    db.scalar.side_effect = [snapshot] + [None] * n_prev + [None, existing_score]

    def mock_scalars(stmt):
        prev = previous_videos or []
        return MagicMock(all=MagicMock(return_value=prev))

    db.scalars = mock_scalars

    def mock_execute(stmt):
        return MagicMock(all=MagicMock(return_value=[]))

    db.execute = mock_execute

    return db


def _make_video(
    published_at_days_ago: float = 10,
    view_count: int = 100_000,
    channel_id: int = 1,
    video_id: int = 1,
) -> tuple[Video, VideoSnapshot, Channel]:
    now = datetime.now(UTC)
    video = Video(
        id=video_id,
        channel_id=channel_id,
        youtube_video_id="test_video_id",
        title="Test Video",
        published_at=now - timedelta(days=published_at_days_ago),
    )
    snapshot = VideoSnapshot(
        video_id=video_id,
        view_count=view_count,
    )
    channel = Channel(
        id=channel_id,
        youtube_channel_id="UCtest",
        title="Test Channel",
        subscriber_count=10_000,
    )
    return video, snapshot, channel


def test_score_with_baseline() -> None:
    video, snapshot, channel = _make_video(published_at_days_ago=10, view_count=200_000)
    now = datetime.now(UTC)
    age_days = (now - video.published_at).total_seconds() / 86400
    expected_vpd = 200_000 / age_days

    prev_video, prev_snapshot, _ = _make_video(
        published_at_days_ago=20, view_count=50_000, video_id=2
    )

    db = _make_mock_db(
        channel=channel,
        snapshot=snapshot,
        previous_videos=[prev_video],
    )
    score = calculate_video_score(db, video)
    assert score is not None
    assert score.age_days is not None
    assert abs(score.views_per_day - expected_vpd) < 1.0
    assert score.is_small_channel_breakout is True
    assert score.outlier_score is not None


def test_score_cold_start() -> None:
    video, snapshot, channel = _make_video(published_at_days_ago=5, view_count=500)
    db = _make_mock_db(channel=channel, snapshot=snapshot, previous_videos=[])
    score = calculate_video_score(db, video)
    assert score is not None
    assert score.channel_baseline_vpd is None
    assert score.outlier_score is not None
    assert score.outlier_score <= 1.5


def test_score_no_snapshot() -> None:
    video, _, channel = _make_video()
    db = _make_mock_db(channel=channel, snapshot=None)
    score = calculate_video_score(db, video)
    assert score is None


def test_small_channel_breakout_true() -> None:
    video, snapshot, channel = _make_video(
        published_at_days_ago=30, view_count=200_000, channel_id=1
    )
    channel.subscriber_count = 5_000
    db = _make_mock_db(channel=channel, snapshot=snapshot, previous_videos=[])
    score = calculate_video_score(db, video)
    assert score is not None
    assert score.is_small_channel_breakout is True


def test_small_channel_breakout_large_channel() -> None:
    video, snapshot, channel = _make_video(
        published_at_days_ago=30, view_count=200_000, channel_id=1
    )
    channel.subscriber_count = 500_000
    db = _make_mock_db(channel=channel, snapshot=snapshot, previous_videos=[])
    score = calculate_video_score(db, video)
    assert score is not None
    assert score.is_small_channel_breakout is False


def test_small_channel_breakout_low_views() -> None:
    video, snapshot, channel = _make_video(
        published_at_days_ago=30, view_count=1_000, channel_id=1
    )
    channel.subscriber_count = 10_000
    db = _make_mock_db(channel=channel, snapshot=snapshot, previous_videos=[])
    score = calculate_video_score(db, video)
    assert score is not None
    assert score.is_small_channel_breakout is False


def test_outlier_score_math() -> None:
    video, snapshot, channel = _make_video(published_at_days_ago=2, view_count=20_000)

    prev_video, prev_snapshot, _ = _make_video(
        published_at_days_ago=30, view_count=30_000, video_id=2
    )
    db = _make_mock_db(
        channel=channel,
        snapshot=snapshot,
        previous_videos=[prev_video],
    )
    score = calculate_video_score(db, video)
    assert score is not None
    assert score.views_per_day is not None
    assert score.outlier_score is not None
    assert isinstance(score.outlier_score, float)