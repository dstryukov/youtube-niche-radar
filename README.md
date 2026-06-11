# YouTube Niche Radar — MVP

Backend and minimal dashboard for monitoring selected YouTube channels, collecting recent videos, saving statistic snapshots, calculating anomaly scores, and preparing AI-based format/niche classification.

## Product goal

The radar should not only show successful videos. It should explain:

- what format worked
- why this video is an anomaly
- whether the format can be faceless
- whether the format can be produced with AI
- how repeatable the format is
- what ideas can be adapted

## Stack

- Backend: FastAPI + SQLAlchemy 2 + Pydantic Settings
- DB: PostgreSQL
- Queue: Celery + Redis
- YouTube: YouTube Data API v3 via API key
- AI classifier: rule-based stub now, LLM structured output later
- Frontend: minimal Next.js dashboard

## Tables

Core MVP:

- `channels`
- `videos`
- `video_snapshots`
- `channel_snapshots`
- `video_scores`
- `formats`
- `niches`
- `ai_classifications`

Operational:

- `task_runs`
- `api_quota_usage`

## Local setup

### Prerequisites

- Docker + Docker Compose
- A YouTube Data API v3 key from [Google Cloud Console](https://console.cloud.google.com/apis/credentials)

### Environment variables

Copy the example env file and set your YouTube API key:

```bash
cp backend/.env.example backend/.env
# Edit backend/.env and set YOUTUBE_API_KEY
```

Available variables:

| Variable | Description | Default |
|---|---|---|
| `DATABASE_URL` | PostgreSQL connection string | `postgresql+psycopg://radar:radar@db:5432/radar` |
| `REDIS_URL` | Redis connection string | `redis://redis:6379/0` |
| `YOUTUBE_API_KEY` | YouTube Data API v3 key | *(required)* |
| `OPENAI_API_KEY` | OpenAI key for AI classification (optional) | *(empty)* |
| `SYNC_RECENT_VIDEO_LIMIT` | Max videos to fetch per sync | `50` |
| `DEFAULT_SYNC_LIMIT` | Default limit when not specified | `50` |
| `QUOTA_WARN_DAILY_UNITS` | Warn threshold for daily API quota | `8000` |
| `API_ENV` | Environment name (development/production) | `development` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Docker Compose

```bash
docker compose up --build
```

This starts: PostgreSQL, Redis, FastAPI (port 8001), Celery worker, and the frontend (port 3000).

### Database migrations

Run schema:

```bash
make migrate
```

Seed format/niche labels:

```bash
make seed
```

Apply indexes (safe to run anytime):

```bash
make migrate-indexes
```

If upgrading from v0.1:

```bash
make migrate-upgrade
make seed
make migrate-indexes
```

### Running tests

```bash
make test
```

Or directly:

```bash
docker compose exec api python -m pytest tests/ -v
```

To run tests locally (without Docker):

```bash
cd backend
pip install -e ".[test]"
python -m pytest tests/ -v
```

## API endpoints

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Health check |
| `POST` | `/channels` | Add a channel manually |
| `POST` | `/channels/import-csv` | Import channels from CSV |
| `GET` | `/channels` | List channels |
| `POST` | `/channels/{id}/sync` | Queue sync for one channel |
| `POST` | `/channels/sync-all` | Queue sync for all active channels |
| `GET` | `/tasks` | List task runs |
| `GET` | `/tasks/{id}` | Get task run details |
| `GET` | `/videos/outliers` | List outlier videos |
| `POST` | `/videos/{id}/classify` | Classify a single video |
| `POST` | `/videos/classify-outliers` | Classify all outlier videos |
| `GET` | `/dashboard/summary` | Dashboard statistics |

Full docs at `http://localhost:8001/docs` (Swagger UI).

## MVP flow

1. Add channels manually with `POST /channels` or upload CSV with `POST /channels/import-csv`.
2. Queue sync with `POST /channels/{id}/sync` or `POST /channels/sync-all`.
3. Worker refreshes channel metadata, reads uploads playlist, fetches latest videos, and stores snapshots.
4. Scores are calculated into `video_scores`.
5. Classify outliers using `POST /videos/classify-outliers`.
6. Read anomalies via `GET /videos/outliers` or dashboard via `GET /dashboard/summary`.

## Scoring v0.2

```text
views_per_day = latest_views / max(video_age_days, 0.25)
views_per_sub = latest_views / subscriber_count
outlier_multiplier = (views_per_day + 1) / (channel_median_views_per_day + 1)
outlier_score = log10(outlier_multiplier)
```

Cold-start channels without enough history use a conservative absolute velocity fallback. The score becomes much more useful after at least 10 historical videos per channel.

Small channel breakout v0.2:

```text
subscriber_count <= 100_000
AND latest_views >= max(50_000, 2 * subscriber_count)
```

## CSV format

See `samples/channels.csv`.

Supported columns: `channel_id`, `handle`, `url`, `tags` (separated by `;`), `notes`.

Single-column CSV files with handles, channel ids, or channel URLs also work.

Empty rows are silently skipped. Malformed rows are reported in the import result's `errors` field.

## Notes

This version does not include a real LLM classifier yet. `ai_classifier.py` contains a deterministic stub so that the product loop and dashboard can be tested before spending tokens.
