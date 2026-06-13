.PHONY: up down migrate migrate-upgrade migrate-indexes migrate-all seed api worker frontend test

up:
	docker compose up --build

down:
	docker compose down

migrate:
	docker compose exec db psql -U radar -d radar -f /migrations/001_init.sql

migrate-upgrade:
	docker compose exec db psql -U radar -d radar -f /migrations/003_upgrade_0_1_to_0_2.sql

migrate-indexes:
	docker compose exec db psql -U radar -d radar -f /migrations/004_add_indexes.sql

seed:
	docker compose exec db psql -U radar -d radar -f /migrations/002_seed_formats.sql

seed-more:
	docker compose exec db psql -U radar -d radar -f /migrations/005_seed_more_formats.sql

migrate-format:
	docker compose exec db psql -U radar -d radar -f /migrations/006_add_classifier_version.sql

# Fresh database setup: core schema + upgrade + indexes + seeds + format migration
migrate-all: migrate migrate-upgrade migrate-indexes seed seed-more migrate-format

api:
	docker compose up api

worker:
	docker compose up worker

frontend:
	docker compose up frontend

test:
	docker compose exec api python -m pytest tests/ -v