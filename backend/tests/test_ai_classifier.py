from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from app.models import Video
from app.services.ai_classifier import (
    ClassificationResult,
    classify_and_save_video,
    classify_video_llm,
    classify_video_stub,
)
from app.services.llm_client import LLMResult


def _make_video(
    video_id: int = 1,
    title: str = "Test Video",
    description: str = "A test video description",
    duration_seconds: int = 300,
) -> Video:
    video = MagicMock(spec=Video)
    video.id = video_id
    video.title = title
    video.description = description
    video.duration_seconds = duration_seconds
    return video


VALID_LLM_JSON = json.dumps(
    {
        "format_label": "tutorial / guide",
        "niche_label": "AI tools",
        "hook_type": "how-to promise",
        "target_audience": "beginners",
        "is_faceless_friendly": True,
        "is_ai_friendly": True,
        "repeatability_score": 0.85,
        "adaptation_ideas": ["Idea 1", "Idea 2"],
        "confidence": 0.9,
        "rationale": "Clear tutorial format with AI focus",
    }
)


class TestClassifyVideoLLM:
    def test_classify_video_llm_success(self):
        video = _make_video()
        with patch("app.services.ai_classifier.settings") as mock_settings, patch("app.services.ai_classifier.get_llm_client") as mock_factory:
            mock_settings.llm_model = "llama-3.3-70b-versatile"
            mock_settings.llm_provider = "groq"
            mock_client = MagicMock()
            mock_client.chat_structured.return_value = LLMResult(
                content=VALID_LLM_JSON,
                model="llama-3.3-70b-versatile",
                usage=None,
            )
            mock_factory.return_value = mock_client
            result, model_name = classify_video_llm(video)
            assert isinstance(result, ClassificationResult)
            assert model_name == "llama-3.3-70b-versatile"
            assert result.format_label == "tutorial / guide"
            assert result.niche_label == "AI tools"
            assert result.hook_type == "how-to promise"
            assert result.target_audience == "beginners"
            assert result.is_faceless_friendly is True
            assert result.is_ai_friendly is True
            assert result.repeatability_score == 0.85
            assert result.adaptation_ideas == ["Idea 1", "Idea 2"]
            assert result.confidence == 0.9
            assert result.rationale != ""

    def test_classify_video_llm_fallback_on_error(self):
        video = _make_video()
        with patch("app.services.ai_classifier.settings") as mock_settings, patch("app.services.ai_classifier.get_llm_client") as mock_factory:
            mock_settings.llm_model = "llama-3.3-70b-versatile"
            mock_client = MagicMock()
            mock_client.chat_structured.side_effect = RuntimeError("API down")
            mock_factory.return_value = mock_client
            result, model_name = classify_video_llm(video)
            assert isinstance(result, ClassificationResult)
            assert model_name == "stub"
            assert result.rationale != ""
            assert result.confidence <= 0.3

    def test_classify_video_llm_fallback_on_bad_json(self):
        video = _make_video()
        with patch("app.services.ai_classifier.settings") as mock_settings, patch("app.services.ai_classifier.get_llm_client") as mock_factory:
            mock_settings.llm_model = "llama-3.3-70b-versatile"
            mock_client = MagicMock()
            mock_client.chat_structured.return_value = LLMResult(
                content="this is not json",
                model="llama-3.3-70b-versatile",
                usage=None,
            )
            mock_factory.return_value = mock_client
            result, model_name = classify_video_llm(video)
            assert isinstance(result, ClassificationResult)
            assert model_name == "stub"
            assert result.confidence <= 0.3

    def test_classify_video_llm_saves_to_db(self):
        video = _make_video()
        mock_db = MagicMock()
        mock_db.scalar.return_value = None
        with patch("app.services.ai_classifier.get_llm_client") as mock_factory:
            mock_client = MagicMock()
            mock_client.chat_structured.return_value = LLMResult(
                content=VALID_LLM_JSON,
                model="llama-3.3-70b-versatile",
                usage=None,
            )
            mock_factory.return_value = mock_client
            result = classify_and_save_video(mock_db, video)
            assert result is not None
            assert mock_db.add.call_count == 3
            mock_db.flush.assert_called()
            mock_db.commit.assert_called_once()
