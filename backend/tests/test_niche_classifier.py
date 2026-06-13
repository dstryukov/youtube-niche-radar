from __future__ import annotations

from app.services.niche_classifier import NICHE_CLASSIFIER_VERSION, classify_niche


def test_ai_niche() -> None:
    result = classify_niche("chatgpt changed my life", "ai generated content with openai", None, None)
    assert result["niche_label"] == "AI"
    assert result["classifier_version"] == "niche_rule_v1"


def test_history_niche() -> None:
    result = classify_niche("ancient rome empire history", "historical documentary", None, None)
    assert result["niche_label"] == "History"


def test_crime_niche() -> None:
    result = classify_niche("the murder of a small town", "crime investigation unsolved", None, None)
    assert result["niche_label"] == "Crime"


def test_finance_niche() -> None:
    result = classify_niche("best stocks to buy now", "investing for beginners finance", None, None)
    assert result["niche_label"] == "Finance"


def test_relationships_niche() -> None:
    result = classify_niche("aita for leaving my job", "relationship advice", None, None)
    assert result["niche_label"] == "Relationships"


def test_technology_niche() -> None:
    result = classify_niche("python programming tutorial", "software development", None, None)
    assert result["niche_label"] == "Technology"


def test_gaming_niche() -> None:
    result = classify_niche("minecraft survival gameplay", "gaming fun", None, None)
    assert result["niche_label"] == "Gaming"


def test_space_niche() -> None:
    result = classify_niche("nasa mars mission", "space exploration universe", None, None)
    assert result["niche_label"] == "Space"


def test_science_niche() -> None:
    result = classify_niche("physics experiment", "scientific research", None, None)
    assert result["niche_label"] == "Science"


def test_health_niche() -> None:
    result = classify_niche("healthy nutrition tips", "wellness diet", None, None)
    assert result["niche_label"] == "Health"


def test_fitness_niche() -> None:
    result = classify_niche("bodybuilding transformation", "fat loss journey", None, None)
    assert result["niche_label"] == "Fitness"


def test_education_niche() -> None:
    result = classify_niche("online course", "study for exam", None, None)
    assert result["niche_label"] == "Education"


def test_business_niche() -> None:
    result = classify_niche("startup marketing tips", "business entrepreneurship", None, None)
    assert result["niche_label"] == "Business"


def test_motivation_niche() -> None:
    result = classify_niche("never give up motivational speech", "success story", None, None)
    assert result["niche_label"] == "Motivation"


def test_news_niche() -> None:
    result = classify_niche("breaking news today", "latest headlines report", None, None)
    assert result["niche_label"] == "News"


def test_politics_niche() -> None:
    result = classify_niche("government election update", "political debate", None, None)
    assert result["niche_label"] == "Politics"


def test_entertainment_niche() -> None:
    result = classify_niche("netflix hollywood movie", "celebrity interview", None, None)
    assert result["niche_label"] == "Entertainment"


def test_self_improvement_niche() -> None:
    result = classify_niche("self improvement habits", "productivity mindset", None, None)
    assert result["niche_label"] == "Self Improvement"


def test_other_niche_fallback() -> None:
    result = classify_niche("random cooking video", None, None, None)
    assert result["niche_label"] == "Other"


def test_other_niche_empty_title() -> None:
    result = classify_niche("", None, None, None)
    assert result["niche_label"] == "Other"


def test_classifier_version_saved() -> None:
    result = classify_niche("python coding", None, None, None)
    assert result["classifier_version"] == "niche_rule_v1"


def test_niche_from_channel_name() -> None:
    result = classify_niche("amazing content", "video description", "tech guru", None)
    assert result["niche_label"] == "Technology"


def test_niche_from_description() -> None:
    result = classify_niche("interesting video", "this is about artificial intelligence and machine learning", None, None)
    assert result["niche_label"] == "AI"
