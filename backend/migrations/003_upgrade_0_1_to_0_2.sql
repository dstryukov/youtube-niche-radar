-- Upgrade helper for users who already ran the first MVP migration.
-- Safe to run after 001_init.sql; most commands use IF EXISTS / IF NOT EXISTS.
-- Normalises task_runs.status default for databases created before v0.2.

DO $$
BEGIN
  IF to_regclass('public.video_metrics') IS NOT NULL AND to_regclass('public.video_scores') IS NULL THEN
    ALTER TABLE video_metrics RENAME TO video_scores;
  END IF;
END $$;

ALTER TABLE channels ADD COLUMN IF NOT EXISTS source VARCHAR(64) DEFAULT 'manual';
ALTER TABLE channels ADD COLUMN IF NOT EXISTS tags JSONB;
ALTER TABLE channels ADD COLUMN IF NOT EXISTS notes TEXT;
ALTER TABLE channels ADD COLUMN IF NOT EXISTS last_synced_at TIMESTAMPTZ;
CREATE INDEX IF NOT EXISTS ix_channels_status ON channels(status);

ALTER TABLE videos ADD COLUMN IF NOT EXISTS duration_seconds INTEGER;
CREATE INDEX IF NOT EXISTS ix_videos_duration_seconds ON videos(duration_seconds);

ALTER TABLE video_scores ADD COLUMN IF NOT EXISTS latest_views BIGINT;
ALTER TABLE video_scores ADD COLUMN IF NOT EXISTS channel_baseline_views DOUBLE PRECISION;
ALTER TABLE video_scores ADD COLUMN IF NOT EXISTS outlier_multiplier DOUBLE PRECISION;
ALTER TABLE video_scores ADD COLUMN IF NOT EXISTS velocity_score DOUBLE PRECISION;
ALTER TABLE video_scores ADD COLUMN IF NOT EXISTS consistency_score DOUBLE PRECISION;
ALTER TABLE video_scores ADD COLUMN IF NOT EXISTS repeatability_score DOUBLE PRECISION;
ALTER TABLE video_scores ADD COLUMN IF NOT EXISTS is_small_channel_breakout BOOLEAN NOT NULL DEFAULT false;
ALTER TABLE video_scores ADD COLUMN IF NOT EXISTS explanation TEXT;
CREATE INDEX IF NOT EXISTS ix_video_scores_calculated_at ON video_scores(calculated_at);
CREATE INDEX IF NOT EXISTS ix_video_scores_views_per_day ON video_scores(views_per_day);
CREATE INDEX IF NOT EXISTS ix_video_scores_views_per_sub ON video_scores(views_per_sub);
CREATE INDEX IF NOT EXISTS ix_video_scores_outlier_multiplier ON video_scores(outlier_multiplier);
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

ALTER TABLE ai_classifications ADD COLUMN IF NOT EXISTS format_id INTEGER REFERENCES formats(id) ON DELETE SET NULL;
ALTER TABLE ai_classifications ADD COLUMN IF NOT EXISTS niche_id INTEGER REFERENCES niches(id) ON DELETE SET NULL;
ALTER TABLE ai_classifications ADD COLUMN IF NOT EXISTS is_faceless_friendly BOOLEAN;
ALTER TABLE ai_classifications ADD COLUMN IF NOT EXISTS is_ai_friendly BOOLEAN;
ALTER TABLE ai_classifications ADD COLUMN IF NOT EXISTS repeatability_score DOUBLE PRECISION;
ALTER TABLE ai_classifications ADD COLUMN IF NOT EXISTS adaptation_ideas JSONB;
CREATE INDEX IF NOT EXISTS ix_ai_classifications_format_id ON ai_classifications(format_id);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_niche_id ON ai_classifications(niche_id);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_faceless ON ai_classifications(is_faceless_friendly);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_ai_friendly ON ai_classifications(is_ai_friendly);
CREATE INDEX IF NOT EXISTS ix_ai_classifications_repeatability_score ON ai_classifications(repeatability_score);

CREATE TABLE IF NOT EXISTS task_runs (
  id SERIAL PRIMARY KEY,
  provider_task_id VARCHAR(128) UNIQUE,
  task_type VARCHAR(64) NOT NULL,
  status VARCHAR(32) NOT NULL DEFAULT 'pending',
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

-- Normalise default for databases that still carry the old 'queued' default from v0.1
ALTER TABLE task_runs ALTER COLUMN status SET DEFAULT 'pending';
UPDATE task_runs SET status = 'pending' WHERE status = 'queued';

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
