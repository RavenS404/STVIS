from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy.orm import Session

from app.models.audit import AuditLog


def record_audit(
    db: Session,
    *,
    action_type: str,
    entity_type: str,
    entity_id: str,
    summary_ar: str,
    summary_en: str,
    actor_user_id: str | None = None,
    actor_device_id: str | None = None,
    actor_role: str | None = None,
    request_id: str | None = None,
    ip_address: str | None = None,
    details: dict[str, Any] | None = None,
) -> AuditLog:
    audit = AuditLog(
        actor_user_id=actor_user_id,
        actor_device_id=actor_device_id,
        actor_role=actor_role,
        action_type=action_type,
        entity_type=entity_type,
        entity_id=str(entity_id),
        summary_ar=summary_ar,
        summary_en=summary_en,
        details_json=details or {},
        request_id=request_id,
        ip_address=ip_address,
        occurred_at=datetime.now(UTC),
    )
    db.add(audit)
    db.flush()
    return audit
