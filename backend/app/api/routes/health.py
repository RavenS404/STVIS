from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.schemas.health import SystemHealthResponse
from app.services.health_service import build_system_health
from common.constants.enums import UserRole

router = APIRouter()


@router.get("/system", response_model=SystemHealthResponse)
def system_health(db: DbSession, _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR))) -> SystemHealthResponse:
    return SystemHealthResponse(**build_system_health(db))
