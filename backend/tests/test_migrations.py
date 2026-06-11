from pathlib import Path

MIGRATIONS = Path(__file__).resolve().parents[1] / "migrations"


def _read(name: str) -> str:
    return (MIGRATIONS / name).read_text(encoding="utf-8")


class Test003Upgrade:
    def test_alters_task_runs_default(self):
        sql = _read("003_upgrade_0_1_to_0_2.sql")
        assert "ALTER TABLE task_runs ALTER COLUMN status SET DEFAULT 'pending'" in sql

    def test_updates_queued_records(self):
        sql = _read("003_upgrade_0_1_to_0_2.sql")
        assert "UPDATE task_runs SET status = 'pending' WHERE status = 'queued'" in sql

    def test_adds_small_channel_breakout_column(self):
        sql = _read("003_upgrade_0_1_to_0_2.sql")
        assert "is_small_channel_breakout" in sql

    def test_creates_small_breakout_index(self):
        sql = _read("003_upgrade_0_1_to_0_2.sql")
        assert "ix_video_scores_small_breakout" in sql

    def test_adds_last_synced_at_column(self):
        sql = _read("003_upgrade_0_1_to_0_2.sql")
        assert "last_synced_at" in sql


class Test004Indexes:
    def test_no_misleading_fresh_db_comment(self):
        sql = _read("004_add_indexes.sql")
        assert "Safe to run on a fresh" not in sql

    def test_documents_003_prerequisite(self):
        sql = _read("004_add_indexes.sql")
        assert "003_upgrade_0_1_to_0_2.sql" in sql

    def test_documents_001_prerequisite(self):
        sql = _read("004_add_indexes.sql")
        assert "001_init.sql" in sql
