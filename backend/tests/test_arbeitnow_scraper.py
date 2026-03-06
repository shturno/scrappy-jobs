"""Tests for the Arbeitnow scraper."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.arbeitnow import fetch_arbeitnow_jobs, _normalize, _is_relevant


def test_is_relevant_brazil_in_location() -> None:
    assert _is_relevant({"remote": False, "location": "São Paulo, Brazil"}) is True
    assert _is_relevant({"remote": False, "location": "Brasil"}) is True


def test_is_relevant_false_for_remote_without_brazil() -> None:
    assert _is_relevant({"remote": True, "location": "Berlin, Germany"}) is False
    assert _is_relevant({"remote": True, "location": "Remote"}) is False
    assert _is_relevant({}) is False


def test_is_relevant_false_for_other_locations() -> None:
    assert _is_relevant({"remote": False, "location": "Berlin, Germany"}) is False
    assert _is_relevant({}) is False


def test_normalize_returns_none_when_no_url() -> None:
    assert _normalize({}) is None
    assert _normalize({"title": "Dev"}) is None


def test_normalize_happy_path() -> None:
    raw: dict[str, Any] = {
        "title": "React Dev",
        "company_name": "Acme",
        "url": "https://arbeitnow.com/jobs/1",
        "description": "hr@acme.com",
    }
    job = _normalize(raw)
    assert job is not None
    assert job["title"] == "React Dev"
    assert job["company"] == "Acme"
    assert job["url"] == "https://arbeitnow.com/jobs/1"
    assert job["email"] == "hr@acme.com"


def _make_response(data: list[dict[str, Any]], status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = {"data": data}
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_JOB: dict[str, Any] = {
    "title": "Frontend Dev",
    "company_name": "TechCo",
    "url": "https://arbeitnow.com/jobs/99",
    "description": "jobs@techco.com",
    "remote": False,
    "location": "São Paulo, Brazil",
}


@pytest.mark.asyncio
async def test_fetch_arbeitnow_jobs_returns_relevant_jobs() -> None:
    mock_response = _make_response([SAMPLE_JOB])

    with patch("app.scrapers.arbeitnow.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.arbeitnow.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_arbeitnow_jobs([], [])

    assert len(jobs) > 0
    assert jobs[0]["title"] == "Frontend Dev"


@pytest.mark.asyncio
async def test_fetch_arbeitnow_jobs_skips_non_brazil() -> None:
    non_brazil: dict[str, Any] = {**SAMPLE_JOB, "remote": False, "location": "Paris"}
    mock_response = _make_response([non_brazil])

    with patch("app.scrapers.arbeitnow.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.arbeitnow.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_arbeitnow_jobs([], [])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_arbeitnow_uses_provided_keywords() -> None:
    """Keywords passed in must be used instead of the default list."""
    mock_response = _make_response([SAMPLE_JOB])

    with patch("app.scrapers.arbeitnow.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.arbeitnow.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await fetch_arbeitnow_jobs(["estagio react", "trainee"], [])

    calls = mock_client.get.call_args_list
    used_keywords = {call.kwargs.get("params", {}).get("search") for call in calls}
    assert "estagio react" in used_keywords
    assert "trainee" in used_keywords


@pytest.mark.asyncio
async def test_fetch_arbeitnow_falls_back_to_default_keywords() -> None:
    """Empty keywords list triggers the hardcoded default list."""
    mock_response = _make_response([])

    with patch("app.scrapers.arbeitnow.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.arbeitnow.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await fetch_arbeitnow_jobs([], [])

    calls = mock_client.get.call_args_list
    used_keywords = {call.kwargs.get("params", {}).get("search") for call in calls}
    assert "react" in used_keywords
