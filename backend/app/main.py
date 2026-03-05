import os
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from app.api.config import router as config_router
from app.api.emails import router as emails_router
from app.api.jobs import router as jobs_router
from app.api.pipeline import router as pipeline_router
from app.database import create_db_and_tables
from app.dependencies.rate_limit import limiter

@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: create database and tables
    create_db_and_tables()
    yield
    # Shutdown logic (if any) would go here

app = FastAPI(title="JobScout API", version="0.1.0", lifespan=lifespan)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "").rstrip("/")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SlowAPIMiddleware)

app.include_router(jobs_router)
app.include_router(emails_router)
app.include_router(config_router)
app.include_router(pipeline_router)





@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
