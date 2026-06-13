from __future__ import annotations

from unittest.mock import MagicMock, patch

from app.services.reclassify_formats import reclassify_all_videos


def test_reclassify_updates_existing() -> None:
    mock_db = MagicMock()
    mock_db.scalars.return_value.all.return_value = [1, 2]

    existing = MagicMock()
    existing.format_label = "Other"
    existing.is_faceless_friendly = True
    existing.is_ai_friendly = True
    existing.classifier_version = None

    def scalar_side_effect(*args, **kwargs):
        if kwargs.get("where") is not None or hasattr(args[1], 'where'):
            return existing
        return None

    mock_db.scalar.side_effect = lambda *a, **kw: existing

    video1 = MagicMock()
    video1.id = 1
    video1.title = "how to bake a cake"
    video1.description = "step by step guide"

    video2 = MagicMock()
    video2.id = 2
    video2.title = "random video"
    video2.description = "just some content"

    mock_db.get.side_effect = lambda _, vid: video1 if vid == 1 else video2

    result = reclassify_all_videos(mock_db)

    assert result["videos_processed"] == 2
    assert result["updated"] == 2
    assert result["failed"] == 0
    assert existing.format_label is not None
    assert existing.classifier_version == "rule_v1"
    mock_db.commit.assert_called_once()


def test_reclassify_creates_missing() -> None:
    mock_db = MagicMock()
    mock_db.scalars.return_value.all.return_value = [1]

    mock_db.scalar.return_value = None

    video = MagicMock()
    video.id = 1
    video.title = "top 10 best songs"
    video.description = None

    mock_db.get.return_value = video

    result = reclassify_all_videos(mock_db)

    assert result["videos_processed"] == 1
    assert result["updated"] == 1
    assert result["failed"] == 0
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
