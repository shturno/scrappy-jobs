"""Tests for orchestrator helpers — deduplication and blocked keyword filter."""

from unittest.mock import patch

import pytest

from app.services.orchestrator import _dedup_by_url, _is_blocked, _load_blocked


def test_is_blocked_matches_keyword_case_insensitive() -> None:
    assert _is_blocked("Senior React Developer", ["senior"]) is True
    assert _is_blocked("SENIOR React Developer", ["senior"]) is True
    assert _is_blocked("Desenvolvedor Pleno React", ["pleno"]) is True


def test_is_blocked_does_not_match_unrelated_title() -> None:
    assert _is_blocked("Desenvolvedor React Júnior", ["senior", "pleno"]) is False
    assert _is_blocked("Frontend Developer", ["senior", "sr", "lead"]) is False


def test_is_blocked_matches_partial_keyword() -> None:
    assert _is_blocked("Sr. Frontend Developer", ["sr"]) is True


def test_is_blocked_empty_blocked_list() -> None:
    assert _is_blocked("Senior Dev", []) is False


def test_is_blocked_empty_title() -> None:
    assert _is_blocked("", ["senior"]) is False


def test_load_blocked_parses_env_var() -> None:
    with patch.dict("os.environ", {"BLOCKED_KEYWORDS": "senior,sr,pleno,pl"}):
        blocked = _load_blocked()
    assert blocked == ["senior", "sr", "pleno", "pl"]


def test_load_blocked_strips_whitespace() -> None:
    with patch.dict("os.environ", {"BLOCKED_KEYWORDS": " senior , sr , pleno "}):
        blocked = _load_blocked()
    assert blocked == ["senior", "sr", "pleno"]


def test_load_blocked_lowercases() -> None:
    with patch.dict("os.environ", {"BLOCKED_KEYWORDS": "SENIOR,SR"}):
        blocked = _load_blocked()
    assert blocked == ["senior", "sr"]


def test_load_blocked_returns_empty_list_when_not_set() -> None:
    with patch.dict("os.environ", {}, clear=True):
        blocked = _load_blocked()
    assert blocked == []


def _job(url: str, title: str = "Dev") -> dict:
    return {"title": title, "company": "X", "url": url, "description": "", "email": None}


def test_dedup_removes_duplicate_urls() -> None:
    jobs = [
        _job("https://example.com/job/1", "Dev A"),
        _job("https://example.com/job/1", "Dev A duplicate"),
        _job("https://example.com/job/2", "Dev B"),
    ]
    result = _dedup_by_url(jobs)
    assert len(result) == 2
    assert result[0]["title"] == "Dev A"
    assert result[1]["title"] == "Dev B"


def test_dedup_keeps_all_when_no_duplicates() -> None:
    jobs = [_job(f"https://example.com/job/{i}") for i in range(5)]
    result = _dedup_by_url(jobs)
    assert len(result) == 5


def test_dedup_skips_jobs_with_empty_url() -> None:
    jobs = [
        {"title": "Dev", "company": "X", "url": "", "description": "", "email": None},
        _job("https://example.com/job/1"),
    ]
    result = _dedup_by_url(jobs)
    assert len(result) == 1
    assert result[0]["url"] == "https://example.com/job/1"


def test_dedup_preserves_order() -> None:
    urls = ["https://c.com/3", "https://a.com/1", "https://b.com/2"]
    jobs = [_job(u) for u in urls]
    result = _dedup_by_url(jobs)
    assert [j["url"] for j in result] == urls


def test_blocked_filter_after_dedup() -> None:
    jobs = [
        _job("https://a.com/1", "Senior React Developer"),
        _job("https://b.com/2", "React Developer Júnior"),
        _job("https://c.com/3", "Pleno Frontend Engineer"),
    ]
    deduped = _dedup_by_url(jobs)
    blocked = ["senior", "pleno"]
    filtered = [j for j in deduped if not _is_blocked(j["title"], blocked)]
    assert len(filtered) == 1
    assert filtered[0]["title"] == "React Developer Júnior"
