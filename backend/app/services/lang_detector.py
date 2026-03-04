"""Language detector — returns 'pt' or 'en' for a given job text."""

import logging
from typing import Literal

from langdetect import detect, LangDetectException

logger = logging.getLogger(__name__)

_PT_KEYWORDS = {"vaga", "empresa", "requisitos", "experiência", "salário"}
_EN_KEYWORDS = {"job", "company", "requirements", "experience", "salary"}

Lang = Literal["pt", "en"]


def _keyword_fallback(text: str) -> Lang:
    lower = text.lower()
    pt_hits = sum(1 for kw in _PT_KEYWORDS if kw in lower)
    en_hits = sum(1 for kw in _EN_KEYWORDS if kw in lower)
    if en_hits > pt_hits:
        return "en"
    return "pt"


def detect_language(title: str, description: str) -> Lang:
    """Detect job language from title + first 500 chars of description.

    Primary: langdetect. Fallback: keyword heuristic. Default: 'pt'.
    """
    text = f"{title} {description[:500]}".strip()
    try:
        lang = detect(text)
        if lang in ("pt", "en"):
            return lang  # type: ignore[return-value]
        return _keyword_fallback(text)
    except LangDetectException:
        logger.warning("langdetect failed, using keyword fallback")
        return _keyword_fallback(text)
