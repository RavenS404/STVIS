from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.schemas.dashboard import DashboardSummary
from app.services.dashboard_service import build_dashboard_summary
from app.services.health_service import build_system_health
from common.constants.enums import UserRole

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
def dashboard_summary(
    db: DbSession,
    _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR)),
) -> DashboardSummary:
    health = build_system_health(db)
    queue_depth = health["components"].get("rabbitmq", {}).get("details", {}).get("queue_depth", 0)
    return DashboardSummary(**build_dashboard_summary(db, queue_depth=queue_depth))
