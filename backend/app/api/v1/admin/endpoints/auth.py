"""Admin authentication endpoints — login, logout, session check."""

import hmac
import os
import time

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel

from backend.app.api.v1.admin.dependencies import require_admin_session

router = APIRouter(prefix="/auth", tags=["admin-auth"])


class LoginRequest(BaseModel):
    """Request body for admin login."""

    password: str


class LoginResponse(BaseModel):
    """Response body for successful admin login."""

    success: bool = True


class SessionResponse(BaseModel):
    """Response body for session status check."""

    authenticated: bool


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, request: Request) -> LoginResponse:
    """Authenticate admin with a single password.

    Compares the provided password against the ``ADMIN_PASSWORD`` environment
    variable using ``hmac.compare_digest`` (timing-safe).  On success, sets
    session data ``{"is_admin": True, "login_at": <timestamp>}``.

    Returns 401 on mismatch without setting any cookie.
    """
    admin_password = os.environ.get("ADMIN_PASSWORD", "")

    if not admin_password:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="ADMIN_PASSWORD environment variable is not configured",
        )

    if not hmac.compare_digest(body.password, admin_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid password",
        )

    # Set session data — Starlette SessionMiddleware serialises to cookie
    request.session.clear()
    request.session["is_admin"] = True
    request.session["login_at"] = time.time()

    return LoginResponse(success=True)


@router.post("/logout", dependencies=[Depends(require_admin_session)])
def logout(request: Request) -> dict:
    """Clear admin session cookie."""
    request.session.clear()
    return {"success": True}


@router.get("/session", response_model=SessionResponse)
def check_session(request: Request) -> SessionResponse:
    """Return current admin authentication status.

    This endpoint is exempt from the ``require_admin_session`` dependency
    so it can report ``authenticated: false`` instead of returning 401.
    """
    is_admin = request.session.get("is_admin") is True
    return SessionResponse(authenticated=is_admin)
