"""Config and pipeline API router."""

import json
import os
from pathlib import Path

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.orchestrator import run_daily_pipeline

router = APIRouter(tags=["config"])

_CONFIG_FILE = Path(__file__).parents[3] / "config.json"


def _read_config_file() -> dict:
    if _CONFIG_FILE.exists():
        return json.loads(_CONFIG_FILE.read_text())
    return {}


def _write_config_file(data: dict) -> None:
    _CONFIG_FILE.write_text(json.dumps(data, indent=2))


class ConfigRead(BaseModel):
    search_keywords: list[str]
    search_cities: list[str]
    daily_limit: int
    sender_name: str
    sender_linkedin: str
    sender_github: str
    sender_portfolio: str


class PipelineSummary(BaseModel):
    scraped: int
    emails_found: int
    sent: int
    errors: int


class ConfigUpdate(BaseModel):
    search_keywords: list[str]
    search_cities: list[str]


@router.get("/api/config", response_model=ConfigRead)
def get_config() -> ConfigRead:
    stored = _read_config_file()
    return ConfigRead(
        search_keywords=stored.get(
            "search_keywords",
            [k.strip() for k in os.getenv("SEARCH_KEYWORDS", "developer").split(",")],
        ),
        search_cities=stored.get(
            "search_cities",
            [c.strip() for c in os.getenv("SEARCH_CITIES", "São Paulo").split(",")],
        ),
        daily_limit=30,
        sender_name=os.getenv("SENDER_NAME", ""),
        sender_linkedin=os.getenv("SENDER_LINKEDIN", ""),
        sender_github=os.getenv("SENDER_GITHUB", ""),
        sender_portfolio=os.getenv("SENDER_PORTFOLIO", ""),
    )


@router.post("/api/config", response_model=ConfigRead)
def update_config(payload: ConfigUpdate) -> ConfigRead:
    stored = _read_config_file()
    stored["search_keywords"] = payload.search_keywords
    stored["search_cities"] = payload.search_cities
    _write_config_file(stored)
    return get_config()


@router.post("/api/pipeline/run", response_model=PipelineSummary)
async def trigger_pipeline() -> PipelineSummary:
    result = await run_daily_pipeline()
    return PipelineSummary(**result)

