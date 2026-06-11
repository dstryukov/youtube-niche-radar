from __future__ import annotations

from unittest.mock import ANY, MagicMock, patch

import pytest

from app.services.ingest import import_channels_from_csv


def _make_db() -> MagicMock:
    db = MagicMock()
    db.add = MagicMock()
    db.flush = MagicMock()
    db.commit = MagicMock()
    db.refresh = MagicMock()
    db.scalar = MagicMock(return_value=None)
    db.scalars = MagicMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    return db


@pytest.fixture
def db() -> MagicMock:
    return _make_db()


def test_csv_single_column_handles(db: MagicMock) -> None:
    csv_text = "@GoogleDevelopers\n@OpenAI\n"
    with patch("app.services.ingest.upsert_channel_from_youtube") as mock_upsert:
        mock_upsert.side_effect = [
            MagicMock(id=1, youtube_channel_id="UC1", title="Google"),
            MagicMock(id=2, youtube_channel_id="UC2", title="OpenAI"),
        ]
        result = import_channels_from_csv(db, csv_text)
    assert result["total_rows"] == 2
    assert result["imported"] == 2
    assert result["skipped"] == 0


def test_csv_mixed_columns(db: MagicMock) -> None:
    csv_text = "channel_id,handle,tags,notes\nUCabc123,@test,ai;tech,seed\n"
    with patch("app.services.ingest.upsert_channel_from_youtube") as mock_upsert:
        mock_upsert.return_value = MagicMock(id=1, youtube_channel_id="UCabc123", title="Test")
        result = import_channels_from_csv(db, csv_text)
    assert result["total_rows"] == 1
    assert result["imported"] == 1
    assert result["errors"] == []


def test_csv_empty_rows_skipped(db: MagicMock) -> None:
    csv_text = "@channel1\n\n\n@channel2\n"
    with patch("app.services.ingest.upsert_channel_from_youtube") as mock_upsert:
        mock_upsert.side_effect = [
            MagicMock(id=1, youtube_channel_id="UC1", title="Ch1"),
            MagicMock(id=2, youtube_channel_id="UC2", title="Ch2"),
        ]
        result = import_channels_from_csv(db, csv_text)
    assert result["total_rows"] == 2
    assert result["imported"] == 2
    assert result["skipped"] == 0


def test_csv_malformed_rows_reported(db: MagicMock) -> None:
    csv_text = "garbage!!!\nnot-a-channel\n"
    with patch("app.services.ingest.upsert_channel_from_youtube") as mock_upsert:
        mock_upsert.side_effect = Exception("YouTube API error")
        result = import_channels_from_csv(db, csv_text)
    assert result["imported"] == 0
    assert result["errors"]


def test_csv_empty_file_returns_empty(db: MagicMock) -> None:
    result = import_channels_from_csv(db, "")
    assert result["total_rows"] == 0
    assert result["imported"] == 0
    assert result["errors"] == []


def test_csv_only_headers_returns_empty(db: MagicMock) -> None:
    result = import_channels_from_csv(db, "channel_id,handle,url,tags,notes\n")
    assert result["total_rows"] == 0
    assert result["imported"] == 0


def test_csv_url_column(db: MagicMock) -> None:
    csv_text = "url\nhttps://www.youtube.com/@GoogleDevelopers\n"
    with patch("app.services.ingest.upsert_channel_from_youtube") as mock_upsert:
        mock_upsert.return_value = MagicMock(id=1, youtube_channel_id="UCxxx", title="Google Devs")
        result = import_channels_from_csv(db, csv_text)
    assert result["total_rows"] == 1
    assert result["imported"] == 1