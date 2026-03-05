"""Tests for the Jooble scraper."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.jooble import fetch_jooble_jobs, _normalize


def test_normalize_returns_none_when_no_link() -> None:
    assert _normalize({}) is None
    assert _normalize({"title": "Dev"}) is None


def test_normalize_happy_path() -> None:
    raw: dict[str, Any] = {
        "title": "React Dev",
        "company": "Acme",
        "link": "https://jooble.org/jobs/1",
        "snippet": "Contact hr@acme.com",
    }
    job = _normalize(raw)
    assert job is not None
    assert job["title"] == "React Dev"
    assert job["company"] == "Acme"
    assert job["url"] == "https://jooble.org/jobs/1"
    assert job["email"] == "hr@acme.com"
    assert job["description"] == "Contact hr@acme.com"


def test_normalize_no_email_in_snippet() -> None:
    raw: dict[str, Any] = {
        "title": "Dev",
        "company": "X",
        "link": "https://jooble.org/jobs/2",
        "snippet": "No email here",
    }
    job = _normalize(raw)
    assert job is not None
    assert job["email"] is None


def _make_response(jobs: list[dict[str, Any]], status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = {"jobs": jobs}
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_JOB: dict[str, Any] = {
    "title": "Frontend Dev",
    "company": "TechCo",
    "link": "https://jooble.org/jobs/99",
    "snippet": "Apply at jobs@techco.com",
}


@pytest.mark.asyncio
async def test_fetch_jooble_jobs_returns_normalized_jobs() -> None:
    mock_response = _make_response([SAMPLE_JOB])

    with patch("app.scrapers.jooble.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.jooble.httpx.AsyncClient") as mock_client_cls, \
         patch.dict("os.environ", {"JOOBLE_API_KEY": "test-key"}):

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_jooble_jobs(["react"], ["São Paulo"])

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Frontend Dev"
    assert jobs[0]["email"] == "jobs@techco.com"


@pytest.mark.asyncio
async def test_fetch_jooble_jobs_returns_empty_without_api_key() -> None:
    with patch.dict("os.environ", {}, clear=True):
        jobs = await fetch_jooble_jobs(["react"], ["São Paulo"])
    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_jooble_jobs_handles_429_silently() -> None:
    mock_response = _make_response([], status=429)

    with patch("app.scrapers.jooble.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.jooble.httpx.AsyncClient") as mock_client_cls, \
         patch.dict("os.environ", {"JOOBLE_API_KEY": "test-key"}):

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_jooble_jobs(["react"], ["São Paulo"])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_jooble_jobs_handles_exception_silently() -> None:
    with patch("app.scrapers.jooble.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.jooble.httpx.AsyncClient") as mock_client_cls, \
         patch.dict("os.environ", {"JOOBLE_API_KEY": "test-key"}):

        mock_client = AsyncMock()
        mock_client.post = AsyncMock(side_effect=Exception("network error"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_jooble_jobs(["react"], ["São Paulo"])

    assert jobs == []
