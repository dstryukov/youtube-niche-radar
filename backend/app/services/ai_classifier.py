from __future__ import annotations

from dataclasses import dataclass, field

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import AIClassification, Format, Niche, Video
from app.services.metrics import calculate_video_score

PROMPT_VERSION = "format-v2"


@dataclass(frozen=True)
class ClassificationResult:
    format_label: str
    niche_label: str
    hook_type: str | None
    target_audience: str | None
    is_faceless_friendly: bool | None
    is_ai_friendly: bool | None
    repeatability_score: float
    adaptation_ideas: list[str] = field(default_factory=list)
    confidence: float = 0.25
    rationale: str = ""


def _contains_any(text: str, values: list[str]) -> bool:
    return any(value in text for value in values)


def classify_video_stub(video: Video) -> ClassificationResult:
    """Rule-based placeholder. Replace with an LLM call using structured output."""
    title = video.title.lower()
    description = (video.description or "").lower()[:1_000]
    text = f"{title}\n{description}"

    if _contains_any(title, ["how to", "tutorial", "guide", "как", "гайд", "инструкция"]):
        fmt = "tutorial / guide"
        hook = "how-to promise"
        repeatability = 0.85
        faceless = True
        ai_friendly = True
    elif _contains_any(title, ["mistakes", "ошибки", "don't", "не делай"]):
        fmt = "mistakes / lessons"
        hook = "avoid failure"
        repeatability = 0.8
        faceless = True
        ai_friendly = True
    elif _contains_any(title, ["review", "обзор", "vs", "versus", "лучший", "best"]):
        fmt = "review / comparison"
        hook = "choice simplification"
        repeatability = 0.75
        faceless = True
        ai_friendly = False
    elif _contains_any(title, ["i tried", "я попробовал", "experiment", "эксперимент"]):
        fmt = "experiment / challenge"
        hook = "curiosity gap"
        repeatability = 0.65
        faceless = False
        ai_friendly = False
    elif _contains_any(title, ["story", "история", "case study", "разбор", "why", "почему"]):
        fmt = "case study / explainer"
        hook = "why it happened"
        repeatability = 0.9
        faceless = True
        ai_friendly = True
    else:
        fmt = "unknown / needs AI"
        hook = None
        repeatability = 0.35
        faceless = None
        ai_friendly = None

    if _contains_any(text, ["ai", "chatgpt", "openai", "midjourney", "нейросет", "ии"]):
        niche = "AI tools"
    elif _contains_any(text, ["money", "business", "startup", "income", "деньги", "бизнес"]):
        niche = "business / money"
    elif _contains_any(text, ["fitness", "health", "workout", "здоров", "трениров"]):
        niche = "health / fitness"
    elif _contains_any(text, ["game", "gaming", "minecraft", "roblox", "игр"]):
        niche = "gaming"
    elif _contains_any(text, ["history", "war", "история", "война"]):
        niche = "history"
    else:
        niche = "unknown"

    ideas = [
        f"Сделать локализованную версию формата: {fmt}",
        "Сузить тему под конкретную аудиторию и добавить более сильный контраст в заголовок",
        "Проверить 3 варианта thumbnail: лицо/объект/до-после",
    ]

    return ClassificationResult(
        format_label=fmt,
        niche_label=niche,
        hook_type=hook,
        target_audience=None,
        is_faceless_friendly=faceless,
        is_ai_friendly=ai_friendly,
        repeatability_score=repeatability,
        adaptation_ideas=ideas,
        confidence=0.3 if fmt != "unknown / needs AI" else 0.15,
        rationale="Rule-based stub based on title and short description. Replace with LLM structured output.",
    )


def _get_or_create_format(db: Session, result: ClassificationResult) -> Format:
    row = db.scalar(select(Format).where(Format.label == result.format_label))
    if row is None:
        row = Format(
            label=result.format_label,
            is_faceless_friendly=result.is_faceless_friendly,
            is_ai_friendly=result.is_ai_friendly,
            repeatability_prior=result.repeatability_score,
        )
        db.add(row)
        db.flush()
    return row


def _get_or_create_niche(db: Session, result: ClassificationResult) -> Niche:
    row = db.scalar(select(Niche).where(Niche.label == result.niche_label))
    if row is None:
        row = Niche(label=result.niche_label)
        db.add(row)
        db.flush()
    return row


def save_classification(db: Session, video: Video, result: ClassificationResult) -> AIClassification:
    fmt = _get_or_create_format(db, result)
    niche = _get_or_create_niche(db, result)
    row = db.scalar(
        select(AIClassification).where(
            AIClassification.video_id == video.id,
            AIClassification.model == "stub",
            AIClassification.prompt_version == PROMPT_VERSION,
        )
    )
    if row is None:
        row = AIClassification(video_id=video.id, model="stub", prompt_version=PROMPT_VERSION)
        db.add(row)

    row.format_id = fmt.id
    row.niche_id = niche.id
    row.format_label = result.format_label
    row.niche_label = result.niche_label
    row.hook_type = result.hook_type
    row.target_audience = result.target_audience
    row.is_faceless_friendly = result.is_faceless_friendly
    row.is_ai_friendly = result.is_ai_friendly
    row.repeatability_score = result.repeatability_score
    row.adaptation_ideas = result.adaptation_ideas
    row.confidence = result.confidence
    row.rationale = result.rationale
    row.raw = result.__dict__
    db.flush()
    calculate_video_score(db, video)
    db.commit()
    db.refresh(row)
    return row


def classify_and_save_video(db: Session, video: Video) -> AIClassification:
    return save_classification(db, video, classify_video_stub(video))
