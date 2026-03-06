"""Tests for the Gupy scraper."""

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.gupy import fetch_gupy_jobs, _extract_email, _normalize


# ---------------------------------------------------------------------------
# Unit tests — helpers
# ---------------------------------------------------------------------------

def test_extract_email_found() -> None:
    text = "Contact us at recruiter@company.com for more info."
    assert _extract_email(text) == "recruiter@company.com"


def test_extract_email_none_when_missing() -> None:
    assert _extract_email("No email here.") is None


def test_extract_email_none_on_empty() -> None:
    assert _extract_email(None) is None
    assert _extract_email("") is None


def test_extract_email_first_match_only() -> None:
    text = "a@x.com and b@y.com"
    assert _extract_email(text) == "a@x.com"


def test_normalize_returns_none_when_no_url() -> None:
    raw: dict[str, Any] = {"name": "Dev", "company": {"name": "Acme"}}
    assert _normalize(raw) is None


def test_normalize_happy_path() -> None:
    raw: dict[str, Any] = {
        "name": "Backend Dev",
        "company": {"name": "Acme"},
        "jobUrl": "https://acme.gupy.io/jobs/1",
        "description": "Send CV to hr@acme.com",
    }
    job = _normalize(raw)
    assert job is not None
    assert job["title"] == "Backend Dev"
    assert job["company"] == "Acme"
    assert job["url"] == "https://acme.gupy.io/jobs/1"
    assert job["email"] == "hr@acme.com"


def test_normalize_missing_company_key() -> None:
    raw: dict[str, Any] = {
        "name": "Dev",
        "jobUrl": "https://x.gupy.io/jobs/2",
    }
    job = _normalize(raw)
    assert job is not None
    assert job["company"] == ""


# ---------------------------------------------------------------------------
# Integration tests — HTTP mocked
# ---------------------------------------------------------------------------

def _make_response(
    data: list[dict[str, Any]],
    total: int | None = None,
    status: int = 200,
) -> MagicMock:
    """Build a mock HTTP response with Gupy's pagination envelope."""
    mock = MagicMock()
    mock.status_code = status
    mock.json.return_value = {
        "data": data,
        "pagination": {"offset": 0, "limit": 50, "total": total if total is not None else len(data)},
    }
    mock.raise_for_status = MagicMock()
    return mock


SAMPLE_JOB: dict[str, Any] = {
    "name": "Python Dev",
    "company": {"name": "TechCo"},
    "jobUrl": "https://techco.gupy.io/jobs/99",
    "description": "Apply at jobs@techco.com",
}


@pytest.mark.asyncio
async def test_fetch_gupy_jobs_returns_normalized_jobs() -> None:
    mock_response = _make_response([SAMPLE_JOB])

    with patch("app.scrapers.gupy.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.gupy.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_gupy_jobs(["python"], ["São Paulo"])

    assert any(j["title"] == "Python Dev" for j in jobs)
    assert any(j["email"] == "jobs@techco.com" for j in jobs)


@pytest.mark.asyncio
async def test_fetch_gupy_jobs_skips_entry_with_no_url() -> None:
    no_url_job: dict[str, Any] = {"name": "Dev", "company": {"name": "X"}}
    mock_response = _make_response([no_url_job])

    with patch("app.scrapers.gupy.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.gupy.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_gupy_jobs(["python"], ["São Paulo"])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_gupy_jobs_handles_429_silently() -> None:
    mock_response = _make_response([], status=429)

    with patch("app.scrapers.gupy.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.gupy.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_gupy_jobs(["python"], ["São Paulo"])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_gupy_jobs_handles_exception_silently() -> None:
    with patch("app.scrapers.gupy.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.gupy.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("network error"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_gupy_jobs(["python"], ["Curitiba"])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_gupy_jobs_paginates_when_total_exceeds_limit() -> None:
    """When total > 50, additional pages should be fetched (up to _MAX_PAGES=3)."""
    job_p2: dict[str, Any] = {**SAMPLE_JOB, "jobUrl": "https://techco.gupy.io/jobs/100"}
    job_p3: dict[str, Any] = {**SAMPLE_JOB, "jobUrl": "https://techco.gupy.io/jobs/101"}

    # total=120 → 3 pages needed (offsets 0, 50, 100)
    page1 = _make_response([SAMPLE_JOB], total=120)
    page2 = _make_response([job_p2], total=120)
    page3 = _make_response([job_p3], total=120)

    responses = [page1, page2, page3, page3]  # extra fallback
    call_idx = 0

    async def mock_get(*args: Any, **kwargs: Any) -> MagicMock:
        nonlocal call_idx
        resp = responses[min(call_idx, len(responses) - 1)]
        call_idx += 1
        return resp

    with patch("app.scrapers.gupy.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.gupy.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await fetch_gupy_jobs(["python"], ["São Paulo"])

    # For 1 keyword × 1 city + 1 remote sweep → at least 2 page-1 requests
    assert call_idx >= 2


@pytest.mark.asyncio
async def test_fetch_gupy_jobs_includes_remote_sweep() -> None:
    """fetch_gupy_jobs should also issue a workplaceType=remote request per keyword."""
    mock_response = _make_response([SAMPLE_JOB])
    params_seen: list[dict[str, Any]] = []

    async def mock_get(*args: Any, **kwargs: Any) -> MagicMock:
        params_seen.append(dict(kwargs.get("params", {})))
        return mock_response

    with patch("app.scrapers.gupy.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.gupy.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = mock_get
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await fetch_gupy_jobs(["python"], ["São Paulo"])

    remote_reqs = [p for p in params_seen if p.get("workplaceType") == "remote"]
    assert len(remote_reqs) >= 1
    city_reqs = [p for p in params_seen if "city" in p]
    assert len(city_reqs) >= 1
