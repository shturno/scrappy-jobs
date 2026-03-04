import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.config import router as config_router
from app.api.emails import router as emails_router
from app.api.jobs import router as jobs_router
from app.api.pipeline import router as pipeline_router
from app.database import create_db_and_tables

app = FastAPI(title="JobScout API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[os.getenv("FRONTEND_URL", "http://localhost:3000")],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(jobs_router)
app.include_router(emails_router)
app.include_router(config_router)
app.include_router(pipeline_router)


@app.on_event("startup")
def on_startup() -> None:
    create_db_and_tables()


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
