# API examples

## Add one channel

```bash
curl -X POST http://localhost:8000/channels \
  -H 'Content-Type: application/json' \
  -d '{"handle":"@GoogleDevelopers","tags":["tech","dev"]}'
```

## Import CSV

CSV columns supported: `channel_id`, `handle`, `url`, `tags`, `notes`.

```bash
curl -X POST http://localhost:8000/channels/import-csv \
  -F 'file=@samples/channels.csv'
```

## Queue sync for one channel

```bash
curl -X POST 'http://localhost:8000/channels/1/sync?limit=50'
```

## Queue sync for all channels

```bash
curl -X POST 'http://localhost:8000/channels/sync-all?limit=50&max_channels=100'
```

## Watch tasks

```bash
curl http://localhost:8000/tasks
curl http://localhost:8000/tasks/1
```

## Classify strongest outliers with stub classifier

```bash
curl -X POST 'http://localhost:8000/videos/classify-outliers?limit=25&min_outlier_score=0.3'
```

## Get outliers

```bash
curl 'http://localhost:8000/videos/outliers?limit=50&small_channel_only=false'
```

## Dashboard summary

```bash
curl http://localhost:8000/dashboard/summary
```
