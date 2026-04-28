"""API v1 router — aggregates all v1 endpoint modules."""

import importlib

from fastapi import APIRouter

health_router = importlib.import_module("backend.app.api.v1.endpoints.health").router
panels_router = importlib.import_module("backend.app.api.v1.endpoints.panels").router
recommendations_router = importlib.import_module("backend.app.api.v1.endpoints.recommendations").router
spectra_router = importlib.import_module("backend.app.api.v1.endpoints.spectra").router
quality_registry_router = importlib.import_module("backend.app.api.v1.endpoints.quality_registry").router
settings_router = importlib.import_module("backend.app.api.v1.endpoints.settings").router
panel_history_router = importlib.import_module("backend.app.api.v1.endpoints.panel_history").router
admin_router = importlib.import_module("backend.app.api.v1.admin.router").admin_router

api_router = APIRouter()

api_router.include_router(health_router, tags=["health"])
api_router.include_router(panels_router, tags=["panels"])
api_router.include_router(recommendations_router, tags=["recommendations"])
api_router.include_router(spectra_router, tags=["spectra"])
api_router.include_router(quality_registry_router, tags=["quality-registry"])
api_router.include_router(admin_router, tags=["admin"])
