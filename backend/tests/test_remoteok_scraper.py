"""Tests for the RemoteOK scraper."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.remoteok import fetch_remoteok_jobs, _normalize, _is_relevant


def test_is_relevant_by_tag() -> None:
    assert _is_relevant({"tags": ["react", "python"]}) is True
    assert _is_relevant({"tags": ["typescript"]}) is True
    assert _is_relevant({"tags": ["devops", "aws"]}) is False
    assert _is_relevant({"tags": []}) is False
    assert _is_relevant({}) is False


def test_normalize_returns_none_when_no_link() -> None:
    assert _normalize({}) is None
    assert _normalize({"title": "Dev"}) is None


def test_normalize_happy_path() -> None:
    raw: dict[str, Any] = {
        "slug": "frontend-dev-123",
        "position": "Frontend Dev",
        "company": "RemoteCo",
        "url": "https://remoteok.com/jobs/123",
        "description": "Email us at hr@remote.co",
    }
    job = _normalize(raw)
    assert job is not None
    assert job["title"] == "Frontend Dev"
    assert job["company"] == "RemoteCo"
    assert job["url"] == "https://remoteok.com/jobs/123"
    assert job["email"] == "hr@remote.co"


def test_normalize_no_email() -> None:
    raw: dict[str, Any] = {
        "position": "Dev",
        "company": "X",
        "url": "https://remoteok.com/jobs/1",
        "description": "",
    }
    job = _normalize(raw)
    assert job is not None
    assert job["email"] is None


def _make_response(items: list[dict[str, Any]], status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = [{"legal": "notice"}] + items
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_JOB: dict[str, Any] = {
    "slug": "react-dev-99",
    "position": "React Dev",
    "company": "TechCo",
    "url": "https://remoteok.com/jobs/99",
    "description": "Apply at jobs@techco.com",
    "tags": ["react", "typescript"],
}


@pytest.mark.asyncio
async def test_fetch_remoteok_jobs_returns_relevant_jobs() -> None:
    mock_response = _make_response([SAMPLE_JOB])

    with patch("app.scrapers.remoteok.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_remoteok_jobs(["react"], ["São Paulo"])

    assert len(jobs) == 1
    assert jobs[0]["title"] == "React Dev"


@pytest.mark.asyncio
async def test_fetch_remoteok_jobs_skips_irrelevant() -> None:
    irrelevant: dict[str, Any] = {**SAMPLE_JOB, "tags": ["devops"]}
    mock_response = _make_response([irrelevant])

    with patch("app.scrapers.remoteok.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_remoteok_jobs([], [])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_remoteok_jobs_handles_exception_silently() -> None:
    with patch("app.scrapers.remoteok.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("DNS error"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_remoteok_jobs([], [])

    assert jobs == []
