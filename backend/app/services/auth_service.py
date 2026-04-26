from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, verify_secret
from app.models.user import User


def authenticate_user(db: Session, username: str, password: str) -> User | None:
    user = db.scalar(select(User).where(User.username == username))
    if not user or not user.is_active:
        return None
    if not verify_secret(password, user.password_hash):
        return None
    user.last_login_at = datetime.now(UTC)
    db.flush()
    return user


def issue_access_token(user: User) -> str:
    return create_access_token(str(user.id), user.role.value)
