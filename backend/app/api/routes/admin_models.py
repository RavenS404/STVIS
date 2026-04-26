from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.schemas.model_profile import ModelProfileRead
from app.services.model_service import list_model_profiles
from common.constants.enums import UserRole

router = APIRouter()


@router.get("", response_model=list[ModelProfileRead])
def models_list(db: DbSession, _user=Depends(require_roles(UserRole.ADMIN, UserRole.SUPERVISOR))):
    return [
        ModelProfileRead(
            id=str(item.id),
            model_key=item.model_key,
            display_name=item.display_name,
            artifact_path=item.artifact_path,
            version=item.version,
            class_map=item.class_map,
            metadata_json=item.metadata_json,
            is_active=item.is_active,
        )
        for item in list_model_profiles(db)
    ]
