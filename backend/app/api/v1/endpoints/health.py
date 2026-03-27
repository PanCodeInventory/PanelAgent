"""Health check endpoint."""

from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """Return service status and version."""
    return {"status": "ok", "version": "1.0.0"}
