"""FlowCyt Panel API — FastAPI application entry point."""

import logging
import os
import secrets
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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

# ---------------------------------------------------------------------------
# Static frontend hosting (single-exe mode)
# ---------------------------------------------------------------------------
# When STATIC_FRONTEND_DIR points at a directory of pre-built Next.js static
# export (out/), mount it at /. The SPA fallback serves index.html for any
# unknown path so client-side routing (e.g. /settings) works on refresh.
# In normal dev/preview mode this is unset and the frontend runs separately.
_static_dir = os.environ.get("STATIC_FRONTEND_DIR", "").strip()
if _static_dir and Path(_static_dir).is_dir():
    _next_dir = Path(_static_dir) / "_next"
    if _next_dir.is_dir():
        app.mount(
            "/_next",
            StaticFiles(directory=_next_dir),
            name="next-static",
        )

    @app.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str):
        """Serve a static file if it exists, otherwise fall back to index.html."""
        candidate = Path(_static_dir) / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        index_html = Path(_static_dir) / "index.html"
        return FileResponse(index_html)

    logger.info("Serving static frontend from %s", _static_dir)
