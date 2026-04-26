from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.models.user import User
from app.schemas.setting import SettingRead, SettingUpdate
from app.services.settings_service import get_settings_map, update_setting
from common.constants.enums import UserRole

router = APIRouter()


@router.get("", response_model=list[SettingRead])
def settings_list(db: DbSession, _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR))):
    return [SettingRead(key=key, value_json=value) for key, value in sorted(get_settings_map(db).items())]


@router.put("/{key}", response_model=SettingRead)
def settings_put(
    key: str,
    payload: SettingUpdate,
    db: DbSession,
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
):
    item = update_setting(db, key, payload.value_json, updated_by_id=str(current_user.id))
    db.commit()
    return SettingRead(key=item.key, value_json=item.value_json, description=item.description, is_secret=item.is_secret)
