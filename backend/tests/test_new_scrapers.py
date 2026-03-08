from unittest.mock import AsyncMock, patch
import pytest
from app.scrapers.amazon import fetch_amazon_jobs
from app.scrapers.google_careers import fetch_google_careers_jobs
from app.scrapers.microsoft_careers import fetch_microsoft_careers_jobs
from app.scrapers.nubank import fetch_nubank_jobs
from app.scrapers.ifood import fetch_ifood_jobs
from app.scrapers.mercadolivre import fetch_mercadolivre_jobs
from app.scrapers.spotify import fetch_spotify_jobs
from app.scrapers.uber import fetch_uber_jobs

@pytest.mark.asyncio
async def test_amazon_returns_list() -> None:
    result = await fetch_amazon_jobs(["dev"], ["São Paulo"])
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_google_careers_returns_list() -> None:
    result = await fetch_google_careers_jobs(["dev"], ["São Paulo"])
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_microsoft_careers_returns_list() -> None:
    result = await fetch_microsoft_careers_jobs(["dev"], ["São Paulo"])
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_nubank_returns_list() -> None:
    result = await fetch_nubank_jobs(["dev"], ["São Paulo"])
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_ifood_returns_list() -> None:
    result = await fetch_ifood_jobs(["dev"], ["São Paulo"])
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_mercadolivre_returns_list() -> None:
    result = await fetch_mercadolivre_jobs(["dev"], ["São Paulo"])
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_spotify_returns_list() -> None:
    result = await fetch_spotify_jobs(["dev"], ["São Paulo"])
    assert isinstance(result, list)

@pytest.mark.asyncio
async def test_uber_returns_list() -> None:
    result = await fetch_uber_jobs(["dev"], ["São Paulo"])
    assert isinstance(result, list)
