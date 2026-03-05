"""Tests for the Adzuna scraper."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.adzuna import fetch_adzuna_jobs, _normalize


def test_normalize_returns_none_when_no_url() -> None:
    assert _normalize({}) is None
    assert _normalize({"title": "Dev"}) is None


def test_normalize_happy_path() -> None:
    raw: dict[str, Any] = {
        "title": "React Dev",
        "company": {"display_name": "Acme"},
        "redirect_url": "https://adzuna.com.br/jobs/1",
        "description": "Contact hr@acme.com",
    }
    job = _normalize(raw)
    assert job is not None
    assert job["title"] == "React Dev"
    assert job["company"] == "Acme"
    assert job["url"] == "https://adzuna.com.br/jobs/1"
    assert job["email"] == "hr@acme.com"


def test_normalize_missing_company() -> None:
    raw: dict[str, Any] = {
        "title": "Dev",
        "redirect_url": "https://adzuna.com.br/jobs/2",
        "description": "",
    }
    job = _normalize(raw)
    assert job is not None
    assert job["company"] == ""


def _make_response(results: list[dict[str, Any]], status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = {"results": results}
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_JOB: dict[str, Any] = {
    "title": "Frontend Dev",
    "company": {"display_name": "TechCo"},
    "redirect_url": "https://adzuna.com.br/jobs/99",
    "description": "Apply at jobs@techco.com",
}


@pytest.mark.asyncio
async def test_fetch_adzuna_jobs_returns_normalized_jobs() -> None:
    mock_response = _make_response([SAMPLE_JOB])

    with patch("app.scrapers.adzuna.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.adzuna.httpx.AsyncClient") as mock_client_cls, \
         patch.dict("os.environ", {"ADZUNA_APP_ID": "id", "ADZUNA_APP_KEY": "key"}):

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_adzuna_jobs(["react"], ["São Paulo"])

    assert any(j["title"] == "Frontend Dev" for j in jobs)


@pytest.mark.asyncio
async def test_fetch_adzuna_jobs_returns_empty_without_keys() -> None:
    with patch.dict("os.environ", {}, clear=True):
        jobs = await fetch_adzuna_jobs(["react"], ["São Paulo"])
    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_adzuna_jobs_handles_429_silently() -> None:
    mock_response = _make_response([], status=429)

    with patch("app.scrapers.adzuna.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.adzuna.httpx.AsyncClient") as mock_client_cls, \
         patch.dict("os.environ", {"ADZUNA_APP_ID": "id", "ADZUNA_APP_KEY": "key"}):

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_adzuna_jobs(["react"], ["São Paulo"])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_adzuna_jobs_handles_exception_silently() -> None:
    with patch("app.scrapers.adzuna.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.adzuna.httpx.AsyncClient") as mock_client_cls, \
         patch.dict("os.environ", {"ADZUNA_APP_ID": "id", "ADZUNA_APP_KEY": "key"}):

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("timeout"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_adzuna_jobs(["react"], ["São Paulo"])

    assert jobs == []
