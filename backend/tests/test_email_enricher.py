"""Tests for the email enricher service."""

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.services.email_enricher import (
    enrich_email,
    _extract_domain,
    _infer_email,
)


# ---------------------------------------------------------------------------
# Unit tests — helpers
# ---------------------------------------------------------------------------

def test_extract_domain_returns_host_for_company_url() -> None:
    assert _extract_domain("https://empresa.com.br/jobs/123") == "empresa.com.br"


def test_extract_domain_returns_none_for_platform() -> None:
    assert _extract_domain("https://empresa.gupy.io/jobs/1") is None
    assert _extract_domain("https://www.linkedin.com/jobs/1") is None
    assert _extract_domain("https://br.indeed.com/jobs/1") is None


def test_extract_domain_returns_none_for_invalid_url() -> None:
    assert _extract_domain("not-a-url") is None
    assert _extract_domain("") is None


def test_infer_email_returns_rh_pattern() -> None:
    email = _infer_email("empresa.com.br")
    assert email == "rh@empresa.com.br"


# ---------------------------------------------------------------------------
# Integration tests — sources mocked
# ---------------------------------------------------------------------------

def _make_http_response(text: str = "", status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.text = text
    return mock


@pytest.mark.asyncio
async def test_enrich_email_finds_email_on_job_page() -> None:
    """Source 1: email found in job page HTML."""
    html = "<html>Contact: recruiter@company.com</html>"
    mock_response = _make_http_response(html)

    with patch("app.services.email_enricher.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.services.email_enricher.httpx.AsyncClient") as mock_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await enrich_email("https://empresa.com.br/jobs/1")

    assert result == "recruiter@company.com"


@pytest.mark.asyncio
async def test_enrich_email_skips_platform_domain_for_hunter() -> None:
    """Platform domains (gupy.io) should skip Hunter/Snov after page fetch fails."""
    mock_response = _make_http_response("no email here")

    with patch("app.services.email_enricher.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.services.email_enricher.httpx.AsyncClient") as mock_cls, \
         patch("app.services.email_enricher._hunter_search", new_callable=AsyncMock) as mock_hunter:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        await enrich_email("https://techco.gupy.io/jobs/99")

    mock_hunter.assert_not_called()


@pytest.mark.asyncio
async def test_enrich_email_falls_back_to_hunter() -> None:
    """Source 2: Hunter.io finds email when page has none."""
    mock_response = _make_http_response("no contact info")

    with patch("app.services.email_enricher.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.services.email_enricher.httpx.AsyncClient") as mock_cls, \
         patch("app.services.email_enricher._hunter_search", new_callable=AsyncMock, return_value="hr@company.com"):

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await enrich_email("https://company.com/jobs/1")

    assert result == "hr@company.com"


@pytest.mark.asyncio
async def test_enrich_email_falls_back_to_inferred_pattern() -> None:
    """Source 4: pattern inference when all API sources fail."""
    mock_response = _make_http_response("no email")

    with patch("app.services.email_enricher.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.services.email_enricher.httpx.AsyncClient") as mock_cls, \
         patch("app.services.email_enricher._hunter_search", new_callable=AsyncMock, return_value=None), \
         patch("app.services.email_enricher._snov_search", new_callable=AsyncMock, return_value=None):

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await enrich_email("https://empresa.com.br/jobs/1")

    assert result == "rh@empresa.com.br"


@pytest.mark.asyncio
async def test_enrich_email_handles_network_error_silently() -> None:
    """Network error on job page fetch should not raise — move to next source."""
    with patch("app.services.email_enricher.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.services.email_enricher.httpx.AsyncClient") as mock_cls, \
         patch("app.services.email_enricher._hunter_search", new_callable=AsyncMock, return_value=None), \
         patch("app.services.email_enricher._snov_search", new_callable=AsyncMock, return_value=None):

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("connection error"))
        mock_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        result = await enrich_email("https://empresa.com.br/jobs/1")

    assert result == "rh@empresa.com.br"


@pytest.mark.asyncio
async def test_hunter_skipped_without_api_key() -> None:
    """Hunter.io should not be called if HUNTER_API_KEY is not set."""
    from app.services.email_enricher import _hunter_search
    with patch.dict(os.environ, {"HUNTER_API_KEY": ""}):
        result = await _hunter_search("empresa.com.br")
    assert result is None
