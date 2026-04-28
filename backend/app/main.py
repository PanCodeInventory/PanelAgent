"""FlowCyt Panel API — FastAPI application entry point."""

import logging
import os
import secrets

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from starlette.middleware.sessions import SessionMiddleware

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    logger.info(
        "Starting FlowCyt Panel API  |  LLM endpoint: %s  |  Model: %s",
        settings.OPENAI_API_BASE,
        settings.OPENAI_MODEL_NAME,
    )
    yield
    logger.info("Shutting down FlowCyt Panel API")


app = FastAPI(
    title="FlowCyt Panel API",
    version="1.0.0",
    description="Hybrid AI tool for multi-color flow cytometry panel design.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in settings.BACKEND_CORS_ORIGINS.split(",") if o.strip()],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

session_secret = os.environ.get("ADMIN_SESSION_SECRET", secrets.token_hex(32))
is_production = os.environ.get("ENVIRONMENT", "development") == "production"

app.add_middleware(
    SessionMiddleware,
    secret_key=session_secret,
    session_cookie="panelagent_admin_session",
    max_age=8 * 60 * 60,
    path="/",
    same_site="lax",
    https_only=is_production,
)

app.include_router(api_router, prefix="/api/v1")
