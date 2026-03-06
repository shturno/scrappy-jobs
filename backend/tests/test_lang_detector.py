"""Tests for the language detector service."""

from unittest.mock import patch

import pytest
from langdetect import LangDetectException

from app.services.lang_detector import detect_language, _keyword_fallback, _title_signal


# ---------------------------------------------------------------------------
# Required 3 cases: clear PT, clear EN, ambiguous
# ---------------------------------------------------------------------------

def test_clear_portuguese() -> None:
    """Clear PT text — langdetect should return 'pt'."""
    title = "Desenvolvedor Backend Sênior"
    description = (
        "Estamos buscando um desenvolvedor para integrar nosso time. "
        "A vaga exige experiência com Python e conhecimento em APIs REST. "
        "A empresa oferece salário competitivo e benefícios. "
        "Envie seu currículo com os requisitos atendidos."
    )
    result = detect_language(title, description)
    assert result == "pt"


def test_clear_english() -> None:
    """Clear EN text — langdetect should return 'en'."""
    title = "Senior Backend Developer"
    description = (
        "We are looking for a developer to join our team. "
        "The job requires experience with Python and REST APIs. "
        "The company offers competitive salary and benefits. "
        "Please send your resume listing all requirements met."
    )
    result = detect_language(title, description)
    assert result == "en"


def test_ambiguous_defaults_to_pt() -> None:
    """Ambiguous text (very short, no clear signal) — must default to 'pt'."""
    with patch("app.services.lang_detector.detect", side_effect=LangDetectException(0, "")):
        result = detect_language("Dev", "ok")
    assert result == "pt"


def test_title_signal_pt() -> None:
    """PT title signals must short-circuit langdetect."""
    with patch("app.services.lang_detector.detect") as mock_detect:
        result = detect_language("Desenvolvedor React Júnior", "")
    assert result == "pt"
    mock_detect.assert_not_called()


def test_title_signal_en() -> None:
    """EN title signals must short-circuit langdetect."""
    with patch("app.services.lang_detector.detect") as mock_detect:
        result = detect_language("Frontend Developer Intern", "")
    assert result == "en"
    mock_detect.assert_not_called()


def test_title_signal_no_match_falls_through() -> None:
    """Title with no signal word should still call langdetect."""
    with patch("app.services.lang_detector.detect", return_value="pt") as mock_detect:
        detect_language("React TypeScript", "algum texto")
    mock_detect.assert_called_once()


# ---------------------------------------------------------------------------
# Keyword fallback unit tests
# ---------------------------------------------------------------------------

def test_keyword_fallback_pt_wins() -> None:
    assert _keyword_fallback("vaga empresa requisitos") == "pt"


def test_keyword_fallback_en_wins() -> None:
    assert _keyword_fallback("job company requirements") == "en"


def test_keyword_fallback_tie_defaults_to_pt() -> None:
    # Same number of PT and EN hits → default "pt"
    assert _keyword_fallback("vaga job") == "pt"


def test_keyword_fallback_no_hits_defaults_to_pt() -> None:
    assert _keyword_fallback("nothing here at all") == "pt"


# ---------------------------------------------------------------------------
# langdetect returns unsupported language → falls back to keywords
# ---------------------------------------------------------------------------

def test_unsupported_lang_falls_back_to_keyword() -> None:
    """If langdetect returns e.g. 'es', use keyword heuristic."""
    with patch("app.services.lang_detector.detect", return_value="es"):
        result = detect_language(
            "Desarrollador",
            "job company requirements experience",  # EN keywords win
        )
    assert result == "en"


# ---------------------------------------------------------------------------
# Only first 500 chars of description are used
# ---------------------------------------------------------------------------

def test_truncates_description_to_800_chars() -> None:
    """Ensure description beyond 800 chars is ignored."""
    short_desc = "vaga empresa requisitos " * 10         # PT signal in first 800
    long_tail = " job company requirements " * 200       # EN noise beyond 800
    full_desc = short_desc + long_tail                   # total >> 800

    with patch("app.services.lang_detector.detect", side_effect=LangDetectException(0, "")):
        result = detect_language("", full_desc)
    assert result == "pt"
