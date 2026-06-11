from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import MagicMock, patch

import pytest

from app.tasks import update_task_status


def test_update_task_status_sets_running() -> None:
    mock_db = MagicMock()
    mock_task_run = MagicMock()
    mock_task_run.status = "pending"
    mock_task_run.started_at = None
    mock_task_run.finished_at = None
    mock_task_run.result = None
    mock_task_run.error = None
    mock_db.get.return_value = mock_task_run

    with patch("app.tasks.SessionLocal", return_value=mock_db):
        update_task_status(1, status="running")

    assert mock_task_run.status == "running"
    assert mock_task_run.started_at is not None
    assert mock_task_run.finished_at is None
    mock_db.commit.assert_called_once()
    mock_db.close.assert_called_once()


def test_update_task_status_sets_success() -> None:
    mock_db = MagicMock()
    mock_task_run = MagicMock()
    mock_task_run.status = "running"
    mock_task_run.started_at = datetime.now(UTC)
    mock_task_run.finished_at = None
    mock_task_run.result = None
    mock_task_run.error = None
    mock_db.get.return_value = mock_task_run

    with patch("app.tasks.SessionLocal", return_value=mock_db):
        update_task_status(1, status="success", result={"videos_found": 10})

    assert mock_task_run.status == "success"
    assert mock_task_run.finished_at is not None
    assert mock_task_run.result == {"videos_found": 10}
    mock_db.commit.assert_called_once()


def test_update_task_status_sets_failed() -> None:
    mock_db = MagicMock()
    mock_task_run = MagicMock()
    mock_task_run.status = "running"
    mock_task_run.started_at = datetime.now(UTC)
    mock_task_run.finished_at = None
    mock_task_run.result = None
    mock_task_run.error = None
    mock_db.get.return_value = mock_task_run

    with patch("app.tasks.SessionLocal", return_value=mock_db):
        update_task_status(1, status="failed", error="Something went wrong")

    assert mock_task_run.status == "failed"
    assert mock_task_run.finished_at is not None
    assert mock_task_run.error == "Something went wrong"


def test_update_task_status_unknown_id_silent() -> None:
    mock_db = MagicMock()
    mock_db.get.return_value = None
    mock_db.commit = MagicMock()
    mock_db.close = MagicMock()

    with patch("app.tasks.SessionLocal", return_value=mock_db):
        update_task_status(999, status="running")

    mock_db.commit.assert_not_called()
    mock_db.close.assert_called_once()


def test_update_task_status_rollback_on_error() -> None:
    mock_db = MagicMock()
    mock_task_run = MagicMock()
    mock_db.get.return_value = mock_task_run
    mock_db.commit.side_effect = Exception("DB error")

    with patch("app.tasks.SessionLocal", return_value=mock_db):
        update_task_status(1, status="success")

    mock_db.rollback.assert_called_once()
    mock_db.close.assert_called_once()