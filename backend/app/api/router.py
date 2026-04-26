from fastapi import APIRouter

from app.api.routes import (
    admin_devices,
    admin_models,
    admin_settings,
    admin_users,
    audit,
    auth,
    cases,
    dashboard,
    evidence,
    health,
    ingest,
    reports,
)

api_router = APIRouter()
api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(ingest.router, prefix="/ingest", tags=["ingest"])
api_router.include_router(dashboard.router, prefix="/dashboard", tags=["dashboard"])
api_router.include_router(cases.router, prefix="/cases", tags=["cases"])
api_router.include_router(evidence.router, prefix="/evidence", tags=["evidence"])
api_router.include_router(reports.router, prefix="/reports", tags=["reports"])
api_router.include_router(health.router, prefix="/health", tags=["health"])
api_router.include_router(audit.router, prefix="/audit", tags=["audit"])
api_router.include_router(admin_users.router, prefix="/admin/users", tags=["admin-users"])
api_router.include_router(admin_devices.router, prefix="/admin/devices", tags=["admin-devices"])
api_router.include_router(admin_settings.router, prefix="/admin/settings", tags=["admin-settings"])
api_router.include_router(admin_models.router, prefix="/admin/models", tags=["admin-models"])
