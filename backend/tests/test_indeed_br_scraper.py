"""Tests for the Indeed BR scraper."""

import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.scrapers.indeed_br import fetch_indeed_br_jobs, _parse_cards, _extract_email


# ---------------------------------------------------------------------------
# Unit tests — HTML parser
# ---------------------------------------------------------------------------

_SAMPLE_HTML = """
<html><body>
  <div data-jk="abc123">
    <h2><a data-jk="abc123" href="/rc/clk?jk=abc123&amp;fccid=x">
      Desenvolvedor React Júnior
    </a></h2>
    <span data-testid="company-name">TechBR Ltda</span>
    <ul data-testid="job-snippet"><li>Contato: rh@techbr.com.br</li></ul>
  </div>
</body></html>
"""

_EMPTY_HTML = "<html><body><div class='no-results'>Nenhuma vaga</div></body></html>"


def test_parse_cards_extracts_title_and_company() -> None:
    jobs = _parse_cards(_SAMPLE_HTML)
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Desenvolvedor React Júnior"
    assert jobs[0]["company"] == "TechBR Ltda"


def test_parse_cards_extracts_email_from_snippet() -> None:
    jobs = _parse_cards(_SAMPLE_HTML)
    assert jobs[0]["email"] == "rh@techbr.com.br"


def test_parse_cards_builds_full_url() -> None:
    jobs = _parse_cards(_SAMPLE_HTML)
    assert jobs[0]["url"].startswith("https://br.indeed.com")


def test_parse_cards_returns_empty_for_no_results() -> None:
    assert _parse_cards(_EMPTY_HTML) == []


def test_extract_email_found() -> None:
    assert _extract_email("envie para rh@empresa.com.br") == "rh@empresa.com.br"


def test_extract_email_none_when_missing() -> None:
    assert _extract_email("sem contato aqui") is None


# ---------------------------------------------------------------------------
# Integration tests — HTTP mocked
# ---------------------------------------------------------------------------

def _make_response(html: str, status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


@pytest.mark.asyncio
async def test_fetch_indeed_br_jobs_returns_parsed_jobs() -> None:
    mock_response = _make_response(_SAMPLE_HTML)

    with patch("app.scrapers.indeed_br.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.indeed_br.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_indeed_br_jobs(["react júnior"], ["São Paulo"])

    assert len(jobs) == 1
    assert jobs[0]["title"] == "Desenvolvedor React Júnior"


@pytest.mark.asyncio
async def test_fetch_indeed_br_disabled_returns_empty() -> None:
    with patch.dict(os.environ, {"ENABLE_INDEED_BR": "false"}):
        jobs = await fetch_indeed_br_jobs(["react"], ["São Paulo"])
    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_indeed_br_handles_429_silently() -> None:
    mock_response = _make_response("", status=429)

    with patch("app.scrapers.indeed_br.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.indeed_br.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_indeed_br_jobs(["react"], ["São Paulo"])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_indeed_br_handles_network_error_silently() -> None:
    with patch("app.scrapers.indeed_br.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.indeed_br.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("connection error"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_indeed_br_jobs(["react"], ["São Paulo"])

    assert jobs == []
