"""Admin authentication dependency — guards all /api/v1/admin/* routes."""

import time

from fastapi import Depends, HTTPException, Request, status


SESSION_TTL_SECONDS = 8 * 60 * 60  # 8 hours


def require_admin_session(request: Request) -> None:
    """FastAPI dependency that rejects requests without a valid admin session.

    Checks that ``request.session["is_admin"]`` is ``True`` **and** that
    the session has not exceeded the 8-hour TTL.

    Raises:
        HTTPException 401: If session is missing, not admin, or expired.
    """
    session = request.session

    if not session.get("is_admin"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin authentication required",
        )

    login_at = session.get("login_at")
    if login_at is not None and (time.time() - login_at) > SESSION_TTL_SECONDS:
        # Session expired — clear it and reject
        request.session.clear()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired",
        )
