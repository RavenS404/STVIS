from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import hash_secret
from app.models.user import User


def list_users(db: Session) -> list[User]:
    return list(db.scalars(select(User).order_by(User.created_at.desc())))


def create_user(db: Session, *, username: str, full_name: str, role, password: str) -> User:
    user = User(
        username=username,
        full_name=full_name,
        role=role,
        password_hash=hash_secret(password),
    )
    db.add(user)
    db.flush()
    return user
