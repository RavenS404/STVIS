from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.setting import SystemSetting
from common.constants.settings import DEFAULT_SYSTEM_SETTINGS
from common.utils.policy import PolicySettings


def get_settings_map(db: Session) -> dict[str, object]:
    current = {item.key: item.value_json for item in db.scalars(select(SystemSetting))}
    merged = dict(DEFAULT_SYSTEM_SETTINGS)
    merged.update(current)
    return merged


def update_setting(db: Session, key: str, value: object, *, description: str | None = None, updated_by_id: str | None = None) -> SystemSetting:
    item = db.get(SystemSetting, key)
    if item is None:
        item = SystemSetting(key=key, value_json=value, description=description, updated_by_id=updated_by_id)
        db.add(item)
    else:
        item.value_json = value
        if description is not None:
            item.description = description
        item.updated_by_id = updated_by_id
    db.flush()
    return item


def load_policy_settings(db: Session) -> PolicySettings:
    settings = get_settings_map(db)
    return PolicySettings(
        violation_min_confidence=float(settings["violation.min_confidence"]),
        violation_review_threshold=float(settings["violation.review_threshold"]),
        violation_direct_issue_threshold=float(settings["violation.direct_issue_threshold"]),
        plate_min_confidence=float(settings["plate.min_confidence"]),
        plate_direct_issue_threshold=float(settings["plate.direct_issue_threshold"]),
        auto_issue_enabled=bool(settings["policy.auto_issue_enabled"]),
        escalate_on_missing_plate=bool(settings["policy.escalate_on_missing_plate"]),
    )
