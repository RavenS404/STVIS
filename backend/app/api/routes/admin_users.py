from fastapi import APIRouter, Depends

from app.api.deps import DbSession, require_roles
from app.schemas.user import UserCreate, UserRead
from app.services.user_service import create_user, list_users
from common.constants.enums import UserRole

router = APIRouter()


@router.get("", response_model=list[UserRead])
def users_list(db: DbSession, _user=Depends(require_roles(UserRole.ADMIN))):
    return [
        UserRead(
            id=str(item.id),
            username=item.username,
            full_name=item.full_name,
            role=item.role,
            is_active=item.is_active,
            last_login_at=item.last_login_at.isoformat() if item.last_login_at else None,
        )
        for item in list_users(db)
    ]


@router.post("", response_model=UserRead)
def users_create(payload: UserCreate, db: DbSession, _user=Depends(require_roles(UserRole.ADMIN))):
    user = create_user(
        db,
        username=payload.username,
        full_name=payload.full_name,
        role=payload.role,
        password=payload.password,
    )
    db.commit()
    return UserRead(
        id=str(user.id),
        username=user.username,
        full_name=user.full_name,
        role=user.role,
        is_active=user.is_active,
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
    )
