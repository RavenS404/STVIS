from sqlalchemy import select

from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.models.audit import AuditLog
from app.schemas.audit import AuditLogRead
from app.schemas.common import PageMeta, PaginatedResponse
from common.constants.enums import UserRole

router = APIRouter()


@router.get("", response_model=PaginatedResponse[AuditLogRead])
def audit_logs(
    db: DbSession,
    _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR)),
    page: int = 1,
    page_size: int = 30,
    entity_id: str | None = None,
    entity_type: str | None = None,
) -> PaginatedResponse[AuditLogRead]:
    filters = []
    if entity_id:
        filters.append(AuditLog.entity_id == entity_id)
    if entity_type:
        filters.append(AuditLog.entity_type == entity_type)
    query = select(AuditLog).where(*filters).order_by(AuditLog.occurred_at.desc())
    items = list(db.scalars(query.offset((page - 1) * page_size).limit(page_size)))
    total = db.query(AuditLog).filter(*filters).count()
    payload = [
        AuditLogRead(
            id=str(item.id),
            action_type=item.action_type,
            entity_type=item.entity_type,
            entity_id=item.entity_id,
            summary_ar=item.summary_ar,
            summary_en=item.summary_en,
            actor_role=item.actor_role,
            occurred_at=item.occurred_at.isoformat(),
            details_json=item.details_json,
        )
        for item in items
    ]
    return PaginatedResponse(items=payload, meta=PageMeta(page=page, page_size=page_size, total=total))
