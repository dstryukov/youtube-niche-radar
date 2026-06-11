CREATE TABLE IF NOT EXISTS channels (
  id SERIAL PRIMARY KEY,
  youtube_channel_id VARCHAR(64) UNIQUE NOT NULL,
  title VARCHAR(512),
  handle VARCHAR(255),
  uploads_playlist_id VARCHAR(64),
  subscriber_count BIGINT,
  view_count BIGINT,
  video_count BIGINT,
  country VARCHAR(8),
  status VARCHAR(32) NOT NULL DEFAULT 'active',
  source VARCHAR(64) DEFAULT 'manual',
  tags JSONB,
  notes TEXT,
  last_synced_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX IF NOT EXISTS ix_channels_youtube_channel_id ON channels(youtube_channel_id);
CREATE INDEX IF NOT EXISTS ix_channels_handle ON channels(handle);
CREATE INDEX IF NOT EXISTS ix_channels_uploads_playlist_id ON channels(uploads_playlist_id);
CREATE INDEX IF NOT EXISTS ix_channels_status ON channels(status);

CREATE TABLE IF NOT EXISTS channel_snapshots (
  id SERIAL PRIMARY KEY,
  channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  subscriber_count BIGINT,
  view_count BIGINT,
  video_count BIGINT,
  raw JSONB
);
CREATE INDEX IF NOT EXISTS ix_channel_snapshots_channel_id ON channel_snapshots(channel_id);
CREATE INDEX IF NOT EXISTS ix_channel_snapshots_observed_at ON channel_snapshots(observed_at);

CREATE TABLE IF NOT EXISTS videos (
  id SERIAL PRIMARY KEY,
  youtube_video_id VARCHAR(32) UNIQUE NOT NULL,
  channel_id INTEGER NOT NULL REFERENCES channels(id) ON DELETE CASCADE,
  title VARCHAR(512) NOT NULL,
  description TEXT,
  published_at TIMESTAMPTZ NOT NULL,
  duration_iso8601 VARCHAR(64),
  duration_seconds INTEGER,
  category_id VARCHAR(32),
  thumbnail_url TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_videos_youtube_video_id ON videos(youtube_video_id);
CREATE INDEX IF NOT EXISTS ix_videos_channel_id ON videos(channel_id);
CREATE INDEX IF NOT EXISTS ix_videos_published_at ON videos(published_at);
CREATE INDEX IF NOT EXISTS ix_videos_duration_seconds ON videos(duration_seconds);

CREATE TABLE IF NOT EXISTS video_snapshots (
  id SERIAL PRIMARY KEY,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  view_count BIGINT,
  like_count BIGINT,
  comment_count BIGINT,
  raw JSONB,
  CONSTRAINT uq_video_snapshot_time UNIQUE(video_id, observed_at)
);
CREATE INDEX IF NOT EXISTS ix_video_snapshots_video_id ON video_snapshots(video_id);
CREATE INDEX IF NOT EXISTS ix_video_snapshots_observed_at ON video_snapshots(observed_at);

CREATE TABLE IF NOT EXISTS video_scores (
  id SERIAL PRIMARY KEY,
  video_id INTEGER NOT NULL UNIQUE REFERENCES videos(id) ON DELETE CASCADE,
  calculated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  age_days DOUBLE PRECISION,
  latest_views BIGINT,
  views_per_day DOUBLE PRECISION,
  views_per_sub DOUBLE PRECISION,
  channel_baseline_vpd DOUBLE PRECISION,
  channel_baseline_views DOUBLE PRECISION,
  outlier_multiplier DOUBLE PRECISION,
  outlier_score DOUBLE PRECISION,
  velocity_score DOUBLE PRECISION,
  consistency_score DOUBLE PRECISION,
  repeatability_score DOUBLE PRECISION,
  is_small_channel_breakout BOOLEAN NOT NULL DEFAULT false,
  explanation TEXT
);
CREATE INDEX IF NOT EXISTS ix_video_scores_video_id ON video_scores(video_id);
CREATE INDEX IF NOT EXISTS ix_video_scores_calculated_at ON video_scores(calculated_at);
CREATE INDEX IF NOT EXISTS ix_video_scores_views_per_day ON video_scores(views_per_day);
CREATE INDEX IF NOT EXISTS ix_video_scores_views_per_sub ON video_scores(views_per_sub);
CREATE INDEX IF NOT EXISTS ix_video_scores_outlier_multiplier ON video_scores(outlier_multiplier);
CREATE INDEX IF NOT EXISTS ix_video_scores_outlier_score ON video_scores(outlier_score);
CREATE INDEX IF NOT EXISTS ix_video_scores_repeatability_score ON video_scores(repeatability_score);
CREATE INDEX IF NOT EXISTS ix_video_scores_small_breakout ON video_scores(is_small_channel_breakout);

CREATE TABLE IF NOT EXISTS formats (
  id SERIAL PRIMARY KEY,
  label VARCHAR(255) UNIQUE NOT NULL,
  description TEXT,
  is_faceless_friendly BOOLEAN,
  is_ai_friendly BOOLEAN,
  repeatability_prior DOUBLE PRECISION,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_formats_label ON formats(label);

CREATE TABLE IF NOT EXISTS niches (
  id SERIAL PRIMARY KEY,
  label VARCHAR(255) UNIQUE NOT NULL,
  parent_label VARCHAR(255),
  description TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_niches_label ON niches(label);
CREATE INDEX IF NOT EXISTS ix_niches_parent_label ON niches(parent_label);

CREATE TABLE IF NOT EXISTS ai_classifications (
  id SERIAL PRIMARY KEY,
  video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
  model VARCHAR(128) NOT NULL,
  prompt_version VARCHAR(64) NOT NULL,
  format_id INTEGER REFERENCES formats(id) ON DELETE SET NULL,
  niche_id INTEGER REFERENCES niches(id) ON DELETE SET NULL,
  format_label VARCHAR(255),
  niche_label VARCHAR(255),
  hook_type VARCHAR(255),
  target_audience VARCHAR(255),
  is_faceless_friendly BOOLEAN,
  is_ai_friendly BOOLEAN,
  repeatability_score DOUBLE PRECISION,
  adaptation_ideas JSONB,
  confidence DOUBLE PRECISION,
  rationale TEXT,
  raw JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  CONSTRAINT uq_ai_classification_version UNIQUE(video_id, model, prompt_version)
);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_video_id ON ai_classifications(video_id);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_format_id ON ai_classifications(format_id);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_niche_id ON ai_classifications(niche_id);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_format_label ON ai_classifications(format_label);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_niche_label ON ai_classifications(niche_label);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_hook_type ON ai_classifications(hook_type);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_faceless ON ai_classifications(is_faceless_friendly);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_ai_friendly ON ai_classifications(is_ai_friendly);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_repeatability_score ON ai_classifications(repeatability_score);

CREATE TABLE IF NOT EXISTS task_runs (
  id SERIAL PRIMARY KEY,
  provider_task_id VARCHAR(128) UNIQUE,
  task_type VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'queued',
  channel_id INTEGER REFERENCES channels(id) ON DELETE SET NULL,
  started_at TIMESTAMPTZ,
  finished_at TIMESTAMPTZ,
  params JSONB,
  result JSONB,
  error TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX IF NOT EXISTS ix_task_runs_provider_task_id ON task_runs(provider_task_id);
CREATE INDEX IF NOT EXISTS ix_task_runs_task_type ON task_runs(task_type);
CREATE INDEX IF NOT EXISTS ix_task_runs_status ON task_runs(status);
CREATE INDEX IF NOT EXISTS ix_task_runs_channel_id ON task_runs(channel_id);

CREATE TABLE IF NOT EXISTS api_quota_usage (
  id SERIAL PRIMARY KEY,
  provider VARCHAR(64) NOT NULL,
  endpoint VARCHAR(128) NOT NULL,
  units INTEGER NOT NULL,
  request_count INTEGER NOT NULL DEFAULT 1,
  related_task_id INTEGER REFERENCES task_runs(id) ON DELETE SET NULL,
  observed_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  raw JSONB
);
CREATE INDEX IF NOT EXISTS ix_api_quota_usage_provider ON api_quota_usage(provider);
CREATE INDEX IF NOT EXISTS ix_api_quota_usage_endpoint ON api_quota_usage(endpoint);
CREATE INDEX IF NOT EXISTS ix_api_quota_usage_observed_at ON api_quota_usage(observed_at);
