from pydantic import BaseModel


class AuditLogRead(BaseModel):
    id: str
    action_type: str
    entity_type: str
    entity_id: str
    summary_ar: str
    summary_en: str
    actor_role: str | None
    occurred_at: str
    details_json: dict
