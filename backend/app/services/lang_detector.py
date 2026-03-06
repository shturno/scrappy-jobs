"""Language detector — returns 'pt' or 'en' for a given job text."""

import logging
from typing import Literal

from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

Lang = Literal["pt", "en"]

_PT_TITLE_SIGNALS = {
    "desenvolvedor", "desenvolvedora", "estágio", "estagio", "estagiário",
    "estagiaria", "júnior", "junior", "analista", "engenheiro", "engenheira",
    "programador", "programadora", "trainee", "técnico", "tecnico",
}

_EN_TITLE_SIGNALS = {
    "developer", "engineer", "intern", "internship", "software",
    "frontend", "backend", "fullstack", "full-stack", "programmer",
    "architect", "lead", "manager",
}

_PT_KEYWORDS = {
    "vaga", "empresa", "requisitos", "experiência", "salário", "benefícios",
    "contratação", "oportunidade", "candidatura", "conhecimentos",
    "habilidades", "formação", "graduação", "superior",
}

_EN_KEYWORDS = {
    "job", "company", "requirements", "experience", "salary", "benefits",
    "hiring", "opportunity", "application", "skills", "knowledge",
    "degree", "bachelor", "position", "role",
}


def _title_signal(title: str) -> Lang | None:
    """Return language if title contains an unambiguous signal word."""
    lower = title.lower()
    words = set(lower.split())
    if words & _PT_TITLE_SIGNALS:
        return "pt"
    if words & _EN_TITLE_SIGNALS:
        return "en"
    return None


def _keyword_fallback(text: str) -> Lang:
    lower = text.lower()
    pt_hits = sum(1 for kw in _PT_KEYWORDS if kw in lower)
    en_hits = sum(1 for kw in _EN_KEYWORDS if kw in lower)
    if en_hits > pt_hits:
        return "en"
    return "pt"


def detect_language(title: str, description: str) -> Lang:
    """Detect job language from title + first 800 chars of description.

    Priority: title signal words → langdetect → keyword heuristic → 'pt'.
    """
    signal = _title_signal(title)
    if signal:
        return signal

    text = f"{title} {description[:800]}".strip()
    try:
        lang = detect(text)
        if lang in ("pt", "en"):
            return lang  # type: ignore[return-value]
        return _keyword_fallback(text)
    except LangDetectException:
        logger.warning("langdetect failed, using keyword fallback")
        return _keyword_fallback(text)
