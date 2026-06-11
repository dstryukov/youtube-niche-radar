.PHONY: up migrate upgrade seed api worker frontend

up:
	docker compose up --build

migrate:
	docker compose exec db psql -U radar -d radar -f /migrations/001_init.sql

upgrade:
	docker compose exec db psql -U radar -d radar -f /migrations/003_upgrade_0_1_to_0_2.sql

seed:
	docker compose exec db psql -U radar -d radar -f /migrations/002_seed_formats.sql

migrate-upgrade:
	docker compose exec db psql -U radar -d radar -f /migrations/003_upgrade_0_1_to_0_2.sql

migrate-indexes:
	docker compose exec db psql -U radar -d radar -f /migrations/004_add_indexes.sql

api:
	docker compose up api

worker:
	docker compose up worker

frontend:
	docker compose up frontend

test:
	docker compose exec api python -m pytest tests/ -v
