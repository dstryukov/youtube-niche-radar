-- Migration 004: additional indexes for query performance
-- Safe to run on a fresh or existing database.

-- video_scores: ensure outlier_score and breakout indexes exist
CREATE INDEX IF NOT EXISTS ix_video_scores_outlier_score ON video_scores(outlier_score);
CREATE INDEX IF NOT EXISTS ix_video_scores_small_breakout ON video_scores(is_small_channel_breakout);

-- additional coverage for joins and lookups
CREATE INDEX IF NOT EXISTS ix_channels_youtube_channel_id ON channels(youtube_channel_id);
CREATE INDEX IF NOT EXISTS ix_channels_handle ON channels(handle);
CREATE INDEX IF NOT EXISTS ix_channels_status ON channels(status);
CREATE INDEX IF NOT EXISTS ix_videos_youtube_video_id ON videos(youtube_video_id);
CREATE INDEX IF NOT EXISTS ix_videos_channel_id ON videos(channel_id);
CREATE INDEX IF NOT EXISTS ix_videos_published_at ON videos(published_at);
CREATE INDEX IF NOT EXISTS ix_video_snapshots_video_id ON video_snapshots(video_id);
CREATE INDEX IF NOT EXISTS ix_channel_snapshots_channel_id ON channel_snapshots(channel_id);

-- task lookup indexes
CREATE INDEX IF NOT EXISTS ix_task_runs_task_type ON task_runs(task_type);
CREATE INDEX IF NOT EXISTS ix_task_runs_status ON task_runs(status);
CREATE INDEX IF NOT EXISTS ix_task_runs_channel_id ON task_runs(channel_id);
CREATE INDEX IF NOT EXISTS ix_task_runs_provider_task_id ON task_runs(provider_task_id);

-- quota usage lookups
CREATE INDEX IF NOT EXISTS ix_api_quota_usage_provider ON api_quota_usage(provider);
CREATE INDEX IF NOT EXISTS ix_api_quota_usage_endpoint ON api_quota_usage(endpoint);
CREATE INDEX IF NOT EXISTS ix_api_quota_usage_observed_at ON api_quota_usage(observed_at);
