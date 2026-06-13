from __future__ import annotations

import re

NICHE_CLASSIFIER_VERSION = "niche_rule_v1"

NICHE_RULES: list[tuple[str, list[str]]] = [
    ("Relationships", ["dating", "girlfriend", "boyfriend", "relationship", "marriage", "breakup", "cheating", "aita", "relationship advice"]),
    ("AI", ["ai", "chatgpt", "openai", "claude", "midjourney", "llm", "artificial intelligence"]),
    ("History", ["history", "historical", "war", "empire", "ancient", "civilization"]),
    ("Crime", ["crime", "killer", "murder", "investigation", "unsolved"]),
    ("Finance", ["stocks", "investing", "finance", "income", "money", "wealth"]),
    ("Self Improvement", ["self improvement", "productivity", "habits", "mindset", "personal growth", "stoicism"]),
    ("Business", ["business", "entrepreneur", "startup", "marketing", "sales", "ecommerce"]),
    ("Motivation", ["motivation", "motivational", "inspirational", "never give up", "success story"]),
    ("Technology", ["technology", "tech", "software", "programming", "coding", "python", "javascript", "apple", "google", "microsoft"]),
    ("Gaming", ["gaming", "game", "minecraft", "fortnite", "gta", "call of duty", "nintendo", "playstation", "xbox"]),
    ("Space", ["space", "nasa", "spacex", "astronomy", "universe", "galaxy", "planet", "mars"]),
    ("Science", ["science", "scientific", "physics", "chemistry", "biology", "experiment", "research"]),
    ("Health", ["health", "healthy", "wellness", "nutrition", "diet", "exercise", "workout"]),
    ("Fitness", ["fitness", "gym", "bodybuilding", "weight loss", "fat loss", "muscle"]),
    ("Education", ["education", "learn", "course", "lesson", "study", "school", "college", "university"]),
    ("News", ["news", "breaking", "headlines", "report", "latest"]),
    ("Politics", ["politics", "political", "government", "election", "democrat", "republican", "president", "congress"]),
    ("Entertainment", ["entertainment", "celebrity", "movie", "tv show", "music", "hollywood", "netflix"]),
]


def _keyword_in_text(keyword: str, text: str) -> bool:
    pattern = re.compile(r"\b" + re.escape(keyword) + r"\b", re.IGNORECASE)
    return bool(pattern.search(text))


def classify_niche(
    title: str,
    description: str | None,
    channel_name: str | None,
    format_label: str | None,
) -> dict:
    text = (title + " " + (description or "") + " " + (channel_name or "")).lower()

    for niche, keywords in NICHE_RULES:
        if any(_keyword_in_text(kw, text) for kw in keywords):
            return {
                "niche_label": niche,
                "classifier_version": NICHE_CLASSIFIER_VERSION,
            }

    return {
        "niche_label": "Other",
        "classifier_version": NICHE_CLASSIFIER_VERSION,
    }
