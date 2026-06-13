from __future__ import annotations

import re

CLASSIFIER_VERSION = "rule_v1"

FORMAT_RULES: list[tuple[str, list[str], bool, bool]] = [
    ("Reddit Story", ["reddit", "aita", "tifu", "relationship advice", "r/"], True, True),
    ("True Crime", ["murder", "crime", "killer", "investigation", "unsolved"], True, True),
    ("Facts", ["facts", "did you know", "interesting fact"], True, True),
    ("Quiz", ["quiz", "guess", "can you answer"], True, True),
    ("Tutorial", ["how to", "guide", "tutorial", "step by step"], True, True),
    ("Reaction", ["reacts", "reaction", "watching", "responds to"], False, False),
    ("History", ["history", "historical", "ancient", "war", "empire"], True, True),
    ("Finance", ["stocks", "investing", "money", "finance", "income", "business"], True, True),
    ("AI Story", ["ai generated", "chatgpt", "midjourney", "artificial intelligence"], True, True),
    ("Before After", ["before and after", "transformation", "then vs now"], True, True),
    ("Motivation", ["motivation", "inspirational", "never give up", "success story"], True, True),
    ("News", ["breaking news", "just in", "headlines", "news update"], True, True),
    ("Case Study", ["case study", "analysis", "deep dive", "postmortem"], True, True),
    ("Storytime", ["storytime", "my story", "let me tell you"], True, True),
    ("Top List", ["top 5", "top 10", "top 20", "ranking", "ranked", "countdown"], True, True),
]


def classify_video(title: str, description: str | None, channel_name: str | None = None) -> dict:
    text = (title + " " + (description or "") + " " + (channel_name or "")).lower()

    for fmt, keywords, faceless, ai_friendly in FORMAT_RULES:
        if any(kw in text for kw in keywords):
            return {
                "format_label": fmt,
                "is_faceless_friendly": faceless,
                "is_ai_friendly": ai_friendly,
                "classifier_version": CLASSIFIER_VERSION,
            }

    # Top List: handle "best X" and "X best" patterns
    if re.search(r'\b\d+\s*(best|worst)\b|\b(best|worst)\s*\d+\b', text):
        return {
            "format_label": "Top List",
            "is_faceless_friendly": True,
            "is_ai_friendly": True,
            "classifier_version": CLASSIFIER_VERSION,
        }

    return {
        "format_label": "Other",
        "is_faceless_friendly": True,
        "is_ai_friendly": True,
        "classifier_version": CLASSIFIER_VERSION,
    }
