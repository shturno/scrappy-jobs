"""Tests for the Google Custom Search scraper."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.google_jobs import fetch_google_jobs, _normalize_result


def test_normalize_result_returns_none_when_no_link() -> None:
    assert _normalize_result({}) is None
    assert _normalize_result({"title": "Dev"}) is None


def test_normalize_result_happy_path() -> None:
    raw: dict[str, Any] = {
        "title": "React Dev – TechCo",
        "link": "https://techco.com/jobs/1",
        "snippet": "Apply at hr@techco.com",
    }
    job = _normalize_result(raw)
    assert job is not None
    assert job["title"] == "React Dev – TechCo"
    assert job["url"] == "https://techco.com/jobs/1"
    assert job["email"] == "hr@techco.com"


def test_normalize_result_company_from_metatag() -> None:
    raw: dict[str, Any] = {
        "title": "Dev",
        "link": "https://example.com/jobs/1",
        "snippet": "",
        "pagemap": {
            "metatags": [{"og:site_name": "Example Corp"}]
        },
    }
    job = _normalize_result(raw)
    assert job is not None
    assert job["company"] == "Example Corp"


def _make_response(items: list[dict[str, Any]], status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = {"items": items}
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_ITEM: dict[str, Any] = {
    "title": "Frontend Dev",
    "link": "https://techco.com/jobs/99",
    "snippet": "jobs@techco.com",
}


@pytest.mark.asyncio
async def test_fetch_google_jobs_returns_normalized_jobs() -> None:
    mock_response = _make_response([SAMPLE_ITEM])

    with patch("app.scrapers.google_jobs.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.google_jobs.httpx.AsyncClient") as mock_client_cls, \
         patch.dict("os.environ", {"GOOGLE_API_KEY": "key", "GOOGLE_CSE_ID": "cse"}):

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_google_jobs(["react"], ["São Paulo"])

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Frontend Dev"


@pytest.mark.asyncio
async def test_fetch_google_jobs_returns_empty_without_keys() -> None:
    with patch.dict("os.environ", {}, clear=True):
        jobs = await fetch_google_jobs(["react"], ["São Paulo"])
    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_google_jobs_handles_429_silently() -> None:
    mock_response = _make_response([], status=429)

    with patch("app.scrapers.google_jobs.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.google_jobs.httpx.AsyncClient") as mock_client_cls, \
         patch.dict("os.environ", {"GOOGLE_API_KEY": "key", "GOOGLE_CSE_ID": "cse"}):

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_google_jobs(["react"], ["SP"])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_google_jobs_handles_exception_silently() -> None:
    with patch("app.scrapers.google_jobs.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.google_jobs.httpx.AsyncClient") as mock_client_cls, \
         patch.dict("os.environ", {"GOOGLE_API_KEY": "key", "GOOGLE_CSE_ID": "cse"}):

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("network error"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_google_jobs(["react"], ["SP"])

    assert jobs == []
