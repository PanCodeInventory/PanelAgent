"""FlowCyt Panel API — FastAPI application entry point."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from backend.app.api.v1.router import api_router
from backend.app.core.config import get_settings

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    settings = get_settings()
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
    allow_origins=["http://localhost:3000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")
