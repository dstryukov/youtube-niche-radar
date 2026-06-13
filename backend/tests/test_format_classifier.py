from __future__ import annotations

from app.services.format_classifier import CLASSIFIER_VERSION, classify_video


def test_reddit_story_detected() -> None:
    result = classify_video("aita for leaving my job", "reddit post about relationship advice", None)
    assert result["format_label"] == "Reddit Story"
    assert result["is_faceless_friendly"] is True
    assert result["is_ai_friendly"] is True
    assert result["classifier_version"] == "rule_v1"


def test_reddit_story_detected_via_r() -> None:
    result = classify_video("r/askreddit what is your secret", None, None)
    assert result["format_label"] == "Reddit Story"


def test_top_list_detected() -> None:
    result = classify_video("top 10 best movies of all time", None, None)
    assert result["format_label"] == "Top List"


def test_top_list_ranking() -> None:
    result = classify_video("ranked every nba player", None, None)
    assert result["format_label"] == "Top List"


def test_tutorial_detected() -> None:
    result = classify_video("how to bake a cake", "step by step guide", None)
    assert result["format_label"] == "Tutorial"


def test_tutorial_detected_via_guide() -> None:
    result = classify_video("complete guide to python", None, None)
    assert result["format_label"] == "Tutorial"


def test_facts_detected() -> None:
    result = classify_video("interesting facts about space", "did you know", None)
    assert result["format_label"] == "Facts"


def test_quiz_detected() -> None:
    result = classify_video("can you answer these questions", "quiz time", None)
    assert result["format_label"] == "Quiz"


def test_reaction_detected() -> None:
    result = classify_video("watching the funniest videos", "reaction video", None)
    assert result["format_label"] == "Reaction"
    assert result["is_faceless_friendly"] is False
    assert result["is_ai_friendly"] is False


def test_true_crime_detected() -> None:
    result = classify_video("the murder of a small town", "crime investigation", None)
    assert result["format_label"] == "True Crime"


def test_history_detected() -> None:
    result = classify_video("ancient rome empire history", None, None)
    assert result["format_label"] == "History"


def test_finance_detected() -> None:
    result = classify_video("best stocks to buy now", "investing for beginners", None)
    assert result["format_label"] == "Finance"


def test_ai_story_detected() -> None:
    result = classify_video("chatgpt changed my life", "ai generated content", None)
    assert result["format_label"] == "AI Story"


def test_before_after_detected() -> None:
    result = classify_video("before and after weight loss", "transformation journey", None)
    assert result["format_label"] == "Before After"


def test_motivation_detected() -> None:
    result = classify_video("never give up motivational speech", None, None)
    assert result["format_label"] == "Motivation"


def test_news_detected() -> None:
    result = classify_video("breaking news today", "headlines update", None)
    assert result["format_label"] == "News"


def test_case_study_detected() -> None:
    result = classify_video("deep dive analysis", "case study of success", None)
    assert result["format_label"] == "Case Study"


def test_storytime_detected() -> None:
    result = classify_video("storytime my worst date", "let me tell you", None)
    assert result["format_label"] == "Storytime"


def test_other_fallback() -> None:
    result = classify_video("random video about cooking pasta", None, None)
    assert result["format_label"] == "Other"


def test_other_fallback_empty_title() -> None:
    result = classify_video("", None, None)
    assert result["format_label"] == "Other"


def test_classifier_version_saved() -> None:
    result = classify_video("how to code", None, None)
    assert result["classifier_version"] == "rule_v1"
