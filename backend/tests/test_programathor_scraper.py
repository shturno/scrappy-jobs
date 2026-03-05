"""Tests for the Programathor scraper."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from bs4 import BeautifulSoup, Tag

from app.scrapers.programathor import (
    fetch_programathor_jobs,
    _parse_cards,
    _is_expired_card,
    _parse_company,
)


def _make_card(title: str, company: str, href: str, expired: bool = False) -> str:
    vencida = '<span class="expired-label">Vencida</span>' if expired else ""
    return f"""
    <div class="cell-list">
      <a href="{href}">
        <div class="row">
          <div class="col-sm-9">
            <div class="cell-list-content">
              <h3 class="text-24">{title}{vencida}
                <span class="new-label">NOVA</span>
              </h3>
              <div class="cell-list-content-icon">
                <span><i class="fa fa-briefcase"></i>{company}</span>
              </div>
            </div>
          </div>
        </div>
      </a>
    </div>
    """


def test_parse_cards_returns_job() -> None:
    html = _make_card("React Dev", "TechCo", "/jobs/1-react-dev")
    jobs = _parse_cards(html)
    assert len(jobs) == 1
    assert jobs[0]["title"] == "React Dev"
    assert jobs[0]["company"] == "TechCo"
    assert jobs[0]["url"] == "https://programathor.com.br/jobs/1-react-dev"


def test_parse_cards_strips_nova_badge() -> None:
    html = _make_card("React Dev", "TechCo", "/jobs/1")
    jobs = _parse_cards(html)
    assert "NOVA" not in jobs[0]["title"]


def test_parse_cards_skips_expired() -> None:
    html = _make_card("Senior Dev", "Acme", "/jobs/2", expired=True)
    jobs = _parse_cards(html)
    assert jobs == []


def test_parse_cards_builds_absolute_url() -> None:
    html = _make_card("Dev", "X", "/jobs/99")
    jobs = _parse_cards(html)
    assert jobs[0]["url"].startswith("https://programathor.com.br")


def test_is_expired_card_true() -> None:
    soup = BeautifulSoup('<div class="cell-list">Vencida Dev</div>', "html.parser")
    card = soup.find("div")
    assert isinstance(card, Tag)
    assert _is_expired_card(card) is True


def test_is_expired_card_false() -> None:
    soup = BeautifulSoup('<div class="cell-list">React Dev</div>', "html.parser")
    card = soup.find("div")
    assert isinstance(card, Tag)
    assert _is_expired_card(card) is False


def _make_http_response(html: str, status: int = 200) -> MagicMock:
    mock = MagicMock()
    mock.status_code = status
    mock.text = html
    mock.raise_for_status = MagicMock()
    return mock


@pytest.mark.asyncio
async def test_fetch_programathor_jobs_returns_jobs() -> None:
    html = _make_card("Frontend Dev", "TechCo", "/jobs/1-frontend")
    mock_response = _make_http_response(html)

    with patch("app.scrapers.programathor.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.programathor.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_programathor_jobs([], [])

    assert any(j["title"] == "Frontend Dev" for j in jobs)


@pytest.mark.asyncio
async def test_fetch_programathor_jobs_handles_404_silently() -> None:
    mock_response = _make_http_response("", status=404)

    with patch("app.scrapers.programathor.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.programathor.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(return_value=mock_response)
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_programathor_jobs([], [])

    assert jobs == []


@pytest.mark.asyncio
async def test_fetch_programathor_jobs_handles_exception_silently() -> None:
    with patch("app.scrapers.programathor.asyncio.sleep", new_callable=AsyncMock), \
         patch("app.scrapers.programathor.httpx.AsyncClient") as mock_client_cls:

        mock_client = AsyncMock()
        mock_client.get = AsyncMock(side_effect=Exception("connection reset"))
        mock_client_cls.return_value.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

        jobs = await fetch_programathor_jobs([], [])

    assert jobs == []
