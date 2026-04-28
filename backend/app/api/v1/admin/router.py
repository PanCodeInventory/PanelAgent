"""Admin sub-router — aggregates all admin endpoint modules."""

import importlib

from fastapi import APIRouter, Depends

from backend.app.api.v1.admin.dependencies import require_admin_session
from backend.app.api.v1.admin.endpoints.auth import router as auth_router
from backend.app.api.v1.admin.endpoints.quality_registry import router as quality_registry_router

settings_router = importlib.import_module("backend.app.api.v1.endpoints.settings").router
panel_history_router = importlib.import_module("backend.app.api.v1.endpoints.panel_history").router

admin_router = APIRouter(prefix="/admin")

admin_router.include_router(auth_router)
admin_router.include_router(
    settings_router,
    tags=["admin-settings"],
    dependencies=[Depends(require_admin_session)],
)
admin_router.include_router(
    panel_history_router,
    tags=["admin-panel-history"],
    dependencies=[Depends(require_admin_session)],
)
admin_router.include_router(quality_registry_router, tags=["admin-quality-registry"])
